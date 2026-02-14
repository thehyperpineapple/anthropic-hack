import logging
import uuid

from fastapi import APIRouter, Form, HTTPException, UploadFile, status

from dependencies import DBSession, TenantID
from models import SourceType
from schemas import InteractionTextRequest, InteractionUploadResponse
from services.order_orchestrator import ContentSafetyError, OrderOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interactions", tags=["interactions"])
orchestrator = OrderOrchestrator()


@router.post(
    "/process-text",
    response_model=InteractionUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def process_text(
    body: InteractionTextRequest,
    tenant_id: TenantID,
    session: DBSession,
) -> InteractionUploadResponse:
    """Accept pre-transcribed text, run AI pipeline, and return the created order summary."""
    try:
        result = await orchestrator.process_text(
            tenant_id=tenant_id,
            customer_id=body.customer_id,
            transcript=body.transcript,
            source_type=body.source_type,
            session=session,
        )
    except ContentSafetyError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Content rejected by safety policy",
        )
    except Exception:
        logger.exception("process_text failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    return InteractionUploadResponse(**result)


@router.post(
    "/upload",
    response_model=InteractionUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_interaction(
    file: UploadFile,
    source_type: SourceType = Form(...),
    customer_id: uuid.UUID = Form(...),
    tenant_id: TenantID = ...,  # type: ignore[assignment]
    session: DBSession = ...,  # type: ignore[assignment]
) -> InteractionUploadResponse:
    """Accept a file upload, run AI pipeline, and return the created order summary."""
    try:
        result = await orchestrator.process_incoming_interaction(
            tenant_id=tenant_id,
            customer_id=customer_id,
            file=file,
            source_type=source_type,
            session=session,
        )
    except ContentSafetyError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Content rejected by safety policy",
        )
    except Exception:
        logger.exception("upload_interaction failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    return InteractionUploadResponse(**result)
