import logging
import uuid
from decimal import Decimal

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


class OrderOrchestrator:
    """Coordinates the full ingest-to-order pipeline.

    Each public method expects a caller-supplied session and manages the
    transaction boundary itself (commit on success, rollback on failure).
    """

    def __init__(self) -> None:
        self.ai = AIService()

    async def process_incoming_interaction(
        self,
        *,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        file: UploadFile,
        source_type: SourceType,
        session: AsyncSession,
    ) -> dict:
        """End-to-end pipeline: ingest -> transcribe -> extract -> order.

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
            # 3. Extract structured order data via LLM
            # ----------------------------------------------------------
            extracted_items = await self.ai.extract_order_data(transcript)

            # ----------------------------------------------------------
            # 4. Persist AI analysis log
            # ----------------------------------------------------------
            analysis_log = AIAnalysisLog(
                interaction_id=interaction.id,
                transcript_text=transcript,
                raw_extraction_json=extracted_items,
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
