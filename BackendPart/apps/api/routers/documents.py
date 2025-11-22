import mimetypes
import os
from pathlib import Path
from typing import Dict, List, Tuple
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException,
    status,
)
from fastapi.responses import FileResponse
import httpx

from apps.api.schemas.document import FileTypesResponse
from apps.api.deps import (
    get_current_user,
    get_document_manager,
    get_audit_manager,
    get_rbac_manager,
    get_user_manager,
    get_workspace_manager,
    require_permission,
)

from database.managers.document_manager import DocumentManager
from database.managers.audit_manager import AuditManager
from database.managers.rbac_manager import RbacManager
from database.managers.user_manager import UserManager
from database.managers.workspace_manager import WorkspaceManager
from apps.core.storage import save_document_file
from apps.core.security import has_document_access

from apps.api.schemas.documents_edit import DocumentEditResponse, DocumentEditRequest
from apps.api.schemas.document_view import DocumentViewResponse
from apps.api.schemas.documents_upload import (
    DocumentUploadFromViewerResponse,
    DocumentModerateRequest,
    DocumentModerateResponse,
)
from apps.api.schemas.documents_search import (
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentSearchItem,
)
from utils.config import DOC_STORAGE_DIR, RAG_API_URL


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentModerateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_and_approve_document_from_viewer(
    title: str = Form(...),
    department_id: int = Form(...),
    tags: list[str] | None = Form(default=None),
    file: UploadFile = File(...),
    user=Depends(require_permission("documents.approve")),
    document_manager: DocumentManager = Depends(get_document_manager),
    audit_manager: AuditManager = Depends(get_audit_manager),
):
    file_name, storage_key, file_size, content_type = await save_document_file(file)

    ingest_payload = {"filename": storage_key}

    try:
        async with httpx.AsyncClient(base_url=RAG_API_URL, timeout=30.0) as client:
            resp = await client.post("/api/ingest", json=ingest_payload)
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to contact RAG service",
        )

    if resp.status_code // 100 != 2:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="RAG service failed to ingest document",
        )

    document, version = await document_manager.create_document_with_version(
        title=title,
        department_id=department_id,
        uploaded_by_id=user.id,
        file_name=file_name,
        file_type=content_type,
        file_size=file_size,
        storage_key=storage_key,
        tags=tags or [],
    )

    await audit_manager.log_event(
        user_id=user.id,
        action="create_document",
        entity_type="document",
        entity_id=str(document.id),
        meta={
            "version_id": str(version.id),
            "file_name": file_name,
            "department_id": department_id,
            "moderation_action": "approve",
            "created_via": "viewer",
        },
    )

    updated_doc, updated_ver = (
        await document_manager.create_new_version_and_update_document(
            document_id=document.id,
            title=title,
            department_id=department_id,
            access_levels=[],
            tags=tags or [],
            status="active",
            is_valid=True,
            uploaded_by_id=user.id,
            change_notes="Approved upload from viewer",
            version_status="approved",
        )
    )

    await audit_manager.log_event(
        user_id=user.id,
        action="update_document",
        entity_type="document",
        entity_id=str(updated_doc.id),
        meta={
            "moderation_action": "approve",
            "version_id": str(updated_ver.id),
        },
    )

    return DocumentModerateResponse(
        document_id=document.id,
        version_id=version.id,
        document_status=document.status,
        version_status=version.status,
    )


@router.post(
    "/search",
    response_model=DocumentSearchResponse,
)
async def search_documents(
    payload: DocumentSearchRequest,
    user=Depends(require_permission("documents.read")),
    document_manager: DocumentManager = Depends(get_document_manager),
    audit_manager: AuditManager = Depends(get_audit_manager),
    workspace_manager: WorkspaceManager = Depends(get_workspace_manager),
):
    query_id = await workspace_manager.create_query(
        user_id=user.id,
        question=payload.query,
        date_from=payload.date_from,
        date_to=payload.date_to,
        department_ids=payload.department_ids,
        only_active=payload.only_active,
    )

    rag_payload = {
        "question": payload.query,
        "top_k": 10,
    }

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(f"{RAG_API_URL}/api/ask", json=rag_payload)
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not contact RAG service: {e}",
        )

    if resp.status_code // 100 != 2:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"RAG service returned error: {resp.status_code}",
        )

    rag_json = resp.json()

    rag_sources = rag_json.get("sources", [])
    rag_answer = rag_json.get("answer")

    search_results: List[Tuple[str, str]] = []
    for src in rag_sources:
        source = src.get("source")
        if not source:
            continue
        snippet = src.get("content", "")
        search_results.append((str(source), snippet))

    if not search_results:
        await audit_manager.log_event(
            user_id=user.id,
            action="search",
            entity_type="workspace_query",
            entity_id=str(query_id),
            meta={
                "query": payload.query,
                "filters": {
                    "date_from": (
                        str(payload.date_from) if payload.date_from else None
                    ),
                    "date_to": str(payload.date_to) if payload.date_to else None,
                    "department_ids": payload.department_ids,
                    "only_active": payload.only_active,
                },
                "results_count": 0,
            },
        )
        return DocumentSearchResponse(query_id=query_id, answer=rag_answer, items=[])

    storage_keys = [os.path.basename(path) for path, _ in search_results]

    storage_key_to_doc_id = await document_manager.get_document_ids_by_storage_keys(
        storage_keys
    )

    doc_ids: List[UUID] = []
    snippets_map: Dict[UUID, str] = {}

    for full_path, snippet in search_results:
        key = os.path.basename(full_path)
        doc_id = storage_key_to_doc_id.get(key)
        if not doc_id:
            continue
        doc_ids.append(doc_id)
        snippets_map[doc_id] = snippet

    if not doc_ids:
        await audit_manager.log_event(
            user_id=user.id,
            action="search",
            entity_type="workspace_query",
            entity_id=str(query_id),
            meta={
                "query": payload.query,
                "filters": {
                    "date_from": (
                        str(payload.date_from) if payload.date_from else None
                    ),
                    "date_to": str(payload.date_to) if payload.date_to else None,
                    "department_ids": payload.department_ids,
                    "only_active": payload.only_active,
                },
                "results_count": 0,
            },
        )
        return DocumentSearchResponse(query_id=query_id, answer=rag_answer, items=[])

    documents = await document_manager.get_documents_by_ids(doc_ids)

    versions_map = await document_manager.get_current_versions_for_documents(doc_ids)

    items: List[DocumentSearchItem] = []

    for doc in documents:
        if not has_document_access(user.access_levels, doc.access_levels):
            continue

        if payload.only_active and not doc.is_valid:
            continue

        if payload.department_ids and doc.department_id not in payload.department_ids:
            continue

        if payload.date_from and doc.upload_date.date() < payload.date_from:
            continue
        if payload.date_to and doc.upload_date.date() > payload.date_to:
            continue

        if payload.tags and not set(payload.tags).intersection(doc.tags):
            continue

        if payload.extensions:
            ver = versions_map.get(doc.id)
            if not ver:
                continue

            file_type = (ver.file_type or "").lower()
            allowed_types = {t.lower() for t in payload.extensions}

            if file_type not in allowed_types:
                continue

        items.append(
            DocumentSearchItem(
                document_id=doc.id,
                title=doc.title,
                snippet=snippets_map.get(doc.id, ""),
                is_actual=doc.is_valid,
                date=doc.upload_date,
                tags=doc.tags,
            )
        )

    await audit_manager.log_event(
        user_id=user.id,
        action="search",
        entity_type="workspace_query",
        entity_id=str(query_id),
        meta={
            "query": payload.query,
            "filters": {
                "date_from": str(payload.date_from) if payload.date_from else None,
                "date_to": str(payload.date_to) if payload.date_to else None,
                "department_ids": payload.department_ids,
                "only_active": payload.only_active,
            },
            "results_count": len(items),
        },
    )

    return DocumentSearchResponse(
        query_id=query_id,
        answer=rag_answer,
        items=items,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentViewResponse,
)
async def get_document_view(
    document_id: str,
    user=Depends(require_permission("documents.read")),
    document_manager: DocumentManager = Depends(get_document_manager),
    audit_manager: AuditManager = Depends(get_audit_manager),
    rbac_manager: RbacManager = Depends(get_rbac_manager),
    user_manager: UserManager = Depends(get_user_manager),
):
    try:
        doc_uuid = UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document id")

    document, version = await document_manager.get_document_with_current_version(
        doc_uuid
    )
    if version is None:
        raise HTTPException(status_code=404, detail="Document version not found")

    if not has_document_access(user.access_levels, document.access_levels):
        raise HTTPException(status_code=404, detail="Document not found")

    department_name = None
    if document.department_id is not None:
        dept = await rbac_manager.get_department_by_id(document.department_id)
        if dept is not None:
            department_name = dept.name

    uploaded_by = None
    if version.uploaded_by_id is not None:
        uploader = await user_manager.get_user_by_id(version.uploaded_by_id)
        if uploader is not None:
            parts = [
                uploader.last_name or "",
                uploader.first_name or "",
                uploader.middle_name or "",
            ]
            uploaded_by = " ".join(p for p in parts if p).strip() or None

    await audit_manager.log_event(
        user_id=user.id,
        action="view",
        entity_type="document",
        entity_id=str(document.id),
        meta={
            "version_id": str(version.id),
        },
    )

    return DocumentViewResponse(
        document_id=document.id,
        title=document.title,
        is_actual=document.is_valid,
        access_levels=document.access_levels,
        department_name=department_name,
        version_id=version.id,
        uploaded_by=uploaded_by,
        upload_date=version.upload_date,
        file_name=version.file_name,
        storage_key=version.storage_key,
    )


@router.get(
    "/{document_id}/preview",
)
async def preview_document_file(
    document_id: str,
    user=Depends(require_permission("documents.read")),
    document_manager: DocumentManager = Depends(get_document_manager),
    audit_manager: AuditManager = Depends(get_audit_manager),
):
    try:
        doc_uuid = UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document id")

    document, version = await document_manager.get_document_with_current_version(
        doc_uuid
    )
    if version is None:
        raise HTTPException(status_code=404, detail="Document version not found")

    if not has_document_access(user.access_levels, document.access_levels):
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = (DOC_STORAGE_DIR / version.storage_key).resolve()

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    mime_type, _ = mimetypes.guess_type(version.file_name)
    if mime_type is None:
        mime_type = version.file_type or "application/octet-stream"

    await audit_manager.log_event(
        user_id=user.id,
        action="view",
        entity_type="document",
        entity_id=str(document.id),
        meta={
            "version_id": str(version.id),
            "preview": True,
        },
    )

    response = FileResponse(path=file_path, media_type=mime_type)
    response.headers["Content-Disposition"] = f'inline; filename="{version.file_name}"'
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"

    return response


@router.post(
    "/{document_id}/edit",
    response_model=DocumentEditResponse,
)
async def edit_document_metadata(
    document_id: str,
    payload: DocumentEditRequest,
    user=Depends(require_permission("documents.approve")),
    document_manager: DocumentManager = Depends(get_document_manager),
    audit_manager: AuditManager = Depends(get_audit_manager),
):
    try:
        doc_uuid = UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document id")

    document, version = await document_manager.get_document_with_current_version(
        doc_uuid
    )
    if version is None:
        raise HTTPException(status_code=404, detail="Document version not found")

    if not has_document_access(user.access_levels, document.access_levels):
        raise HTTPException(status_code=404, detail="Document not found")

    updated_doc, updated_ver = (
        await document_manager.create_new_version_and_update_document(
            document_id=doc_uuid,
            title=payload.title,
            department_id=payload.department_id,
            access_levels=payload.access_levels,
            tags=payload.tags,
            status=None,
            is_valid=None,
            uploaded_by_id=user.id,
            change_notes=payload.comment,
        )
    )

    uploaded_by_parts = [
        getattr(user, "last_name", None),
        getattr(user, "first_name", None),
        getattr(user, "middle_name", None),
    ]
    uploaded_by = " ".join(p for p in uploaded_by_parts if p) or None

    await audit_manager.log_event(
        user_id=user.id,
        action="update_document",
        entity_type="document",
        entity_id=str(updated_doc.id),
        meta={
            "reason": "manual_edit",
            "title": updated_doc.title,
            "department_id": updated_doc.department_id,
            "category": updated_doc.category,
            "access_levels": updated_doc.access_levels,
            "tags": updated_doc.tags,
            "version_id": str(updated_ver.id),
            "change_notes": payload.comment,
        },
    )

    return DocumentEditResponse(
        document_id=updated_doc.id,
        version_id=updated_ver.id,
        version=updated_ver.version,
        title=updated_doc.title,
        department_id=updated_doc.department_id,
        category=updated_doc.category,
        access_levels=updated_doc.access_levels,
        tags=updated_doc.tags,
        is_actual=updated_doc.is_valid,
        upload_date=updated_ver.upload_date,
        uploaded_by=uploaded_by,
        file_name=updated_ver.file_name,
        storage_key=updated_ver.storage_key,
        change_notes=updated_ver.change_notes,
    )


@router.get(
    "/file-type/get",
    response_model=FileTypesResponse,
)
async def get_all_file_types(
    user=Depends(require_permission("documents.read")),
    document_manager: DocumentManager = Depends(get_document_manager),
):
    file_types = await document_manager.get_all_file_types()

    return FileTypesResponse(types=file_types)


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    user=Depends(require_permission("documents.read")),
    document_manager: DocumentManager = Depends(get_document_manager),
):
    try:
        doc_uuid = UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document id")

    document, version = await document_manager.get_document_with_current_version(
        doc_uuid
    )
    if version is None:
        raise HTTPException(status_code=404, detail="Document version not found")

    if not has_document_access(user.access_levels, document.access_levels):
        raise HTTPException(status_code=404, detail="Document not found")

    storage_key = version.storage_key
    file_path = os.path.join(DOC_STORAGE_DIR, storage_key)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        file_path,
        media_type=version.file_type or "application/octet-stream",
        filename=version.file_name,
    )
