import logging
import uuid
from decimal import Decimal

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import (
    AIAnalysisLog,
    Interaction,
    InteractionStatus,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    SourceType,
)
from services.ai_service import AIService
from services.anomaly_service import detect_anomalies

logger = logging.getLogger(__name__)

# Module-level flag for the one-time startup warning about missing safety key.
_safety_key_warned: bool = False


class ContentSafetyError(Exception):
    """Raised when content fails safety verification in strict mode."""


class OrderOrchestrator:
    """Coordinates the full ingest-to-order pipeline.

    Each public method expects a caller-supplied session and manages the
    transaction boundary itself (commit on success, rollback on failure).
    """

    def __init__(self) -> None:
        self.ai = AIService()
        self._warn_missing_safety_key()

    @staticmethod
    def _warn_missing_safety_key() -> None:
        """Log a one-time warning if WHITE_CIRCLE_API_KEY is absent and safety is enabled."""
        global _safety_key_warned
        if _safety_key_warned:
            return
        _safety_key_warned = True
        safety_mode = settings.SAFETY_MODE
        if not settings.WHITE_CIRCLE_API_KEY and safety_mode != "off":
            logger.warning(
                "WHITE_CIRCLE_API_KEY is not set and SAFETY_MODE=%s. "
                "Content safety checks will be skipped until a key is provided.",
                safety_mode,
            )

    async def process_incoming_interaction(
        self,
        *,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        file: UploadFile,
        source_type: SourceType,
        session: AsyncSession,
    ) -> dict:
        """End-to-end pipeline: ingest -> transcribe -> safety -> extract -> order.

        Returns a summary dict consumed by the router layer.
        """
        try:
            # ----------------------------------------------------------
            # 1. Persist the incoming interaction  (status = PENDING)
            # ----------------------------------------------------------
            interaction = Interaction(
                tenant_id=tenant_id,
                customer_id=customer_id,
                source_type=source_type,
                raw_asset_url=file.filename,
                status=InteractionStatus.PENDING,
            )
            session.add(interaction)
            await session.flush()  # materialise interaction.id

            # ----------------------------------------------------------
            # 2. Transcribe  (voice -> text)
            # ----------------------------------------------------------
            transcript = await self.ai.transcribe_audio(
                file_url=file.filename or ""
            )

            # ----------------------------------------------------------
            # 2b. Content safety check  (White Circle)
            #
            # Controlled by SAFETY_MODE env var:
            #   "strict" -> block unsafe content (raise ContentSafetyError)
            #   "log"    -> warn but continue  (default)
            #   "off"    -> skip entirely
            # ----------------------------------------------------------
            safety_verdict: dict | None = None
            safety_mode = settings.SAFETY_MODE

            if safety_mode == "off":
                logger.debug("Content safety check skipped (SAFETY_MODE=off)")
            elif not settings.WHITE_CIRCLE_API_KEY:
                logger.debug(
                    "Content safety check skipped — WHITE_CIRCLE_API_KEY not set"
                )
            else:
                safety_result = await self.ai.verify_content_safety(transcript)
                safety_verdict = safety_result
                is_unsafe = safety_result.get("decision") == "block"

                if safety_mode == "strict" and is_unsafe:
                    reason = safety_result.get("reason", "unsafe content detected")
                    logger.warning(
                        "Content safety BLOCKED interaction (strict mode): %s",
                        reason,
                    )
                    raise ContentSafetyError(
                        f"Content blocked by safety policy: {reason}"
                    )
                elif is_unsafe:
                    logger.warning(
                        "Content safety flagged interaction (log mode): %s",
                        safety_result.get("reason", "no reason provided"),
                    )

            # ----------------------------------------------------------
            # 3. Extract structured order data via LLM
            # ----------------------------------------------------------
            extracted_items = await self.ai.extract_order_data(transcript)

            # ----------------------------------------------------------
            # 4. Persist AI analysis log
            #
            # The safety_verdict (if any) is stored alongside extracted
            # items inside the raw_extraction_json column:
            #   {
            #     "extracted_items": [ ... ],
            #     "safety_verdict":  { ... } | null
            #   }
            # ----------------------------------------------------------
            analysis_log = AIAnalysisLog(
                interaction_id=interaction.id,
                transcript_text=transcript,
                raw_extraction_json={
                    "extracted_items": extracted_items,
                    "safety_verdict": safety_verdict,
                },
                confidence_score=Decimal("0.9200"),
            )
            session.add(analysis_log)

            # ----------------------------------------------------------
            # 5. Resolve SKUs -> products and build order items
            # ----------------------------------------------------------
            skus = [item["sku"] for item in extracted_items]
            result = await session.execute(
                select(Product).where(
                    Product.tenant_id == tenant_id,
                    Product.sku.in_(skus),
                )
            )
            product_map: dict[str, Product] = {
                p.sku: p for p in result.scalars().all()
            }

            order = Order(
                tenant_id=tenant_id,
                customer_id=customer_id,
                interaction_id=interaction.id,
                status=OrderStatus.DRAFT,
                total_amount=Decimal("0"),
            )
            session.add(order)
            await session.flush()  # materialise order.id

            total = Decimal("0")
            order_item_objects: list[OrderItem] = []

            for raw in extracted_items:
                product = product_map.get(raw["sku"])
                if product is None:
                    logger.warning(
                        "SKU %s not found for tenant %s — skipping",
                        raw["sku"],
                        tenant_id,
                    )
                    continue

                qty = int(raw["qty"])
                unit_price = product.price
                line_total = unit_price * qty
                total += line_total

                oi = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=qty,
                    unit_price=unit_price,
                )
                session.add(oi)
                order_item_objects.append(oi)

            order.total_amount = total

            # ----------------------------------------------------------
            # 6. Anomaly detection  ("White Circle" logic)
            # ----------------------------------------------------------
            anomalies = detect_anomalies(order.id, order_item_objects)
            if anomalies:
                order.status = OrderStatus.FLAGGED
                for a in anomalies:
                    session.add(a)

            # ----------------------------------------------------------
            # 7. Mark interaction as processed
            # ----------------------------------------------------------
            interaction.status = InteractionStatus.PROCESSED

            await session.commit()

            logger.info(
                "Interaction %s processed -> order %s (%d items, %d anomalies)",
                interaction.id,
                order.id,
                len(order_item_objects),
                len(anomalies),
            )

            return {
                "interaction_id": interaction.id,
                "order_id": order.id,
                "status": order.status.value,
                "anomalies_detected": len(anomalies),
            }

        except ContentSafetyError:
            await session.rollback()
            try:
                if interaction.id is not None:  # type: ignore[possibly-undefined]
                    interaction.status = InteractionStatus.FAILED
                    await session.commit()
            except Exception:
                await session.rollback()
            raise

        except Exception:
            await session.rollback()
            # Mark the interaction as FAILED if it was already flushed
            try:
                if interaction.id is not None:  # type: ignore[possibly-undefined]
                    interaction.status = InteractionStatus.FAILED
                    await session.commit()
            except Exception:
                await session.rollback()
            logger.exception("Failed to process interaction")
            raise
