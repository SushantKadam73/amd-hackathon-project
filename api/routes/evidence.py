"""GRC Platform - Evidence API Routes.

Endpoints for evidence artifact upload, listing, and mapping to controls.
Supports file upload of PDF, PNG, JPG, DOCX formats.
"""

import hashlib
import os
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, UploadFile

from api.database import (
    compute_checksum,
    create_evidence,
    create_mapping,
    get_control,
    get_evidence,
    get_mapping,
    get_supported_extensions,
    is_supported_file_type,
    list_evidence,
    list_mappings_by_evidence,
)
from api.models import (
    ErrorResponse,
    EvidenceListResponse,
    EvidenceMappingListResponse,
    EvidenceMappingResponse,
    EvidenceResponse,
    MapToControlRequest,
    MapToControlResponse,
)

from config import get_config

config = get_config()

router = APIRouter(prefix="/api/v1/evidence", tags=["Evidence"])

# Maximum upload size (50 MB)
MAX_UPLOAD_SIZE = 50 * 1024 * 1024


@router.get(
    "",
    response_model=EvidenceListResponse,
    summary="List all evidence artifacts",
)
async def get_evidence_list() -> EvidenceListResponse:
    """Retrieve all uploaded evidence artifacts.

    Returns a list sorted by upload date (newest first).
    """
    try:
        items = list_evidence()
        evidence_items = [
            EvidenceResponse(
                id=e["id"],
                name=e["name"],
                file_path=e.get("file_path"),
                file_type=e.get("file_type"),
                file_size=e.get("file_size"),
                checksum=e.get("checksum"),
                content_text=e.get("content_text"),
                uploaded_by=e.get("uploaded_by"),
                uploaded_at=e.get("uploaded_at"),
            )
            for e in items
        ]
        return EvidenceListResponse(items=evidence_items, total=len(evidence_items))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve evidence artifacts: {str(e)}",
        )


@router.get(
    "/{evidence_id}",
    response_model=EvidenceResponse,
    responses={
        200: {"description": "Evidence artifact details"},
        404: {"description": "Evidence not found", "model": ErrorResponse},
    },
    summary="Get evidence artifact by ID",
)
async def get_evidence_by_id(evidence_id: str) -> EvidenceResponse:
    """Retrieve a single evidence artifact by its UUID.

    Returns full metadata including file info, checksum, and content text.
    """
    try:
        evidence = get_evidence(evidence_id)
        if not evidence:
            raise HTTPException(
                status_code=404,
                detail=f"Evidence artifact with id '{evidence_id}' not found",
            )
        return EvidenceResponse(
            id=evidence["id"],
            name=evidence["name"],
            file_path=evidence.get("file_path"),
            file_type=evidence.get("file_type"),
            file_size=evidence.get("file_size"),
            checksum=evidence.get("checksum"),
            content_text=evidence.get("content_text"),
            uploaded_by=evidence.get("uploaded_by"),
            uploaded_at=evidence.get("uploaded_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve evidence artifact: {str(e)}",
        )


@router.post(
    "",
    response_model=EvidenceResponse,
    status_code=201,
    responses={
        201: {"description": "Evidence artifact created"},
        400: {"description": "Invalid file type", "model": ErrorResponse},
        422: {"description": "Validation error", "model": ErrorResponse},
    },
    summary="Upload an evidence artifact",
)
async def upload_evidence(
    request: Request,
    file: UploadFile,
    uploaded_by: Optional[str] = None,
) -> EvidenceResponse:
    """Upload an evidence artifact file.

    Accepts PDF, PNG, JPG, and DOCX files. The file is saved to disk,
    its content is extracted (for PDF/DOCX), a checksum is computed,
    and metadata is stored in the database.

    Args:
        file: The uploaded file (multipart/form-data).
        uploaded_by: Optional user UUID string.
    """
    # Validate filename
    if not file.filename:
        raise HTTPException(
            status_code=422,
            detail="Filename is required",
        )

    # Check file type
    if not is_supported_file_type(file.filename):
        supported = ", ".join(get_supported_extensions())
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{os.path.splitext(file.filename)[1]}'. "
                f"Accepted types: {supported}"
            ),
        )

    # Create upload directory if needed
    upload_dir = config.storage.upload_dir
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename to prevent collisions
    file_ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_name)

    # Read file content
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=422,
            detail=f"File size exceeds maximum of {MAX_UPLOAD_SIZE // (1024*1024)} MB",
        )

    # Save file to disk
    with open(file_path, "wb") as f:
        f.write(content)

    # Compute checksum
    checksum = hashlib.sha256(content).hexdigest()

    # Extract text content for PDF/DOCX
    content_text = _extract_text(content, file.filename, file_ext)

    # Determine file type category
    file_type = file_ext.lower().lstrip(".")
    if file_type in ("jpg", "jpeg"):
        file_type = "jpeg"

    client_ip = request.client.host if request.client else None

    try:
        evidence = create_evidence(
            name=file.filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            checksum=checksum,
            content_text=content_text,
            uploaded_by=uploaded_by,
            ip_address=client_ip,
        )
        return EvidenceResponse(
            id=evidence["id"],
            name=evidence["name"],
            file_path=evidence.get("file_path"),
            file_type=evidence.get("file_type"),
            file_size=evidence.get("file_size"),
            checksum=evidence.get("checksum"),
            content_text=evidence.get("content_text"),
            uploaded_by=evidence.get("uploaded_by"),
            uploaded_at=evidence.get("uploaded_at"),
        )
    except Exception as e:
        # Clean up file on failure
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create evidence record: {str(e)}",
        )


@router.get(
    "/{evidence_id}/mappings",
    response_model=EvidenceMappingListResponse,
    responses={
        200: {"description": "List of mappings for the evidence artifact"},
        404: {"description": "Evidence not found", "model": ErrorResponse},
    },
    summary="List all control mappings for an evidence artifact",
)
async def get_evidence_mappings(evidence_id: str) -> EvidenceMappingListResponse:
    """Retrieve all control mappings for a specific evidence artifact.

    Returns a list of evidence-to-control mappings with control details
    including control reference ID and title.
    """
    try:
        evidence = get_evidence(evidence_id)
        if not evidence:
            raise HTTPException(
                status_code=404,
                detail=f"Evidence artifact with id '{evidence_id}' not found",
            )

        mappings = list_mappings_by_evidence(evidence_id)
        items = [
            EvidenceMappingResponse(
                id=m["id"],
                evidence_id=m["evidence_id"],
                control_id=m["control_id"],
                control_ref_id=m.get("control_ref_id"),
                control_title=m.get("control_title"),
                weightage=m["weightage"],
                artifact_type=m["artifact_type"],
                mapping_status=m["mapping_status"],
                mapped_at=m.get("mapped_at"),
            )
            for m in mappings
        ]
        return EvidenceMappingListResponse(items=items, total=len(items))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve evidence mappings: {str(e)}",
        )


@router.post(
    "/{evidence_id}/map-to-control",
    response_model=MapToControlResponse,
    status_code=201,
    responses={
        201: {"description": "Mapping created"},
        400: {"description": "Bad request", "model": ErrorResponse},
        404: {"description": "Evidence or control not found", "model": ErrorResponse},
        422: {"description": "Validation error", "model": ErrorResponse},
    },
    summary="Map evidence to a control",
)
async def map_evidence_to_control(
    evidence_id: str,
    body: MapToControlRequest,
    request: Request,
) -> MapToControlResponse:
    """Map an evidence artifact to a control with a specific weightage.

    Each mapping creates an evidence_control_mapping record with
    status 'pending'. The weightage must match the artifact type
    requirement defined for the target control.
    """
    try:
        # Verify evidence exists
        evidence = get_evidence(evidence_id)
        if not evidence:
            raise HTTPException(
                status_code=404,
                detail=f"Evidence artifact with id '{evidence_id}' not found",
            )

        # Verify control exists
        control = get_control(body.control_id)
        if not control:
            raise HTTPException(
                status_code=404,
                detail=f"Control with id '{body.control_id}' not found",
            )

        client_ip = request.client.host if request.client else None

        mapping = create_mapping(
            evidence_id=evidence_id,
            control_id=body.control_id,
            weightage=body.weightage,
            artifact_type=body.artifact_type,
            ip_address=client_ip,
        )

        return MapToControlResponse(
            id=mapping["id"],
            evidence_id=mapping["evidence_id"],
            control_id=mapping["control_id"],
            weightage=mapping["weightage"],
            artifact_type=mapping["artifact_type"],
            mapping_status=mapping["mapping_status"],
            mapped_at=mapping.get("mapped_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create mapping: {str(e)}",
        )


@router.get(
    "/mappings/{mapping_id}",
    response_model=EvidenceMappingResponse,
    responses={
        200: {"description": "Mapping details"},
        404: {"description": "Mapping not found", "model": ErrorResponse},
    },
    summary="Get a single evidence-control mapping by ID",
)
async def get_mapping_by_id(mapping_id: str) -> EvidenceMappingResponse:
    """Retrieve a single evidence-to-control mapping by its UUID.

    Returns full mapping details including evidence and control info.
    """
    try:
        mapping = get_mapping(mapping_id)
        if not mapping:
            raise HTTPException(
                status_code=404,
                detail=f"Mapping with id '{mapping_id}' not found",
            )
        # Try to enrich with control details from list_mappings_by_evidence
        enhanced = None
        try:
            mappings = list_mappings_by_evidence(mapping["evidence_id"])
            for m in mappings:
                if m["id"] == mapping_id:
                    enhanced = m
                    break
        except Exception:
            pass

        source = enhanced or mapping
        return EvidenceMappingResponse(
            id=source["id"],
            evidence_id=source["evidence_id"],
            control_id=source["control_id"],
            control_ref_id=source.get("control_ref_id"),
            control_title=source.get("control_title"),
            weightage=source["weightage"],
            artifact_type=source["artifact_type"],
            mapping_status=source["mapping_status"],
            mapped_at=source.get("mapped_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve mapping: {str(e)}",
        )


def _extract_text(
    content: bytes,
    filename: str,
    ext: str,
) -> Optional[str]:
    """Extract text content from an uploaded file.

    Supports PDF and DOCX files. For images and other types, returns None.

    Args:
        content: Raw file content bytes.
        filename: Original filename.
        ext: Lowercase file extension with leading dot.

    Returns:
        Optional[str]: Extracted text or None.
    """
    try:
        if ext == ".pdf":
            return _extract_pdf_text(content)
        elif ext == ".docx":
            return _extract_docx_text(content)
        elif ext in (".png", ".jpg", ".jpeg"):
            return None  # Image text extraction via OCR (requires pytesseract)
    except Exception:
        # Text extraction failure should not block upload
        pass
    return None


def _extract_pdf_text(content: bytes) -> Optional[str]:
    """Extract text from a PDF file using PyPDF2.

    Args:
        content: Raw PDF content bytes.

    Returns:
        Optional[str]: Extracted text or None.
    """
    try:
        from io import BytesIO

        from PyPDF2 import PdfReader

        reader = PdfReader(BytesIO(content))
        text_parts: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts) if text_parts else None
    except ImportError:
        return None


def _extract_docx_text(content: bytes) -> Optional[str]:
    """Extract text from a DOCX file using python-docx.

    Args:
        content: Raw DOCX content bytes.

    Returns:
        Optional[str]: Extracted text or None.
    """
    try:
        from io import BytesIO

        from docx import Document

        doc = Document(BytesIO(content))
        text_parts: list[str] = []
        for para in doc.paragraphs:
            if para.text:
                text_parts.append(para.text)
        return "\n".join(text_parts) if text_parts else None
    except ImportError:
        return None
