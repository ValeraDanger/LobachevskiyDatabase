from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List
from uuid import UUID

from apps.api.deps import get_audit_manager, get_current_user, get_document_manager, get_workspace_manager
from apps.api.schemas.collection import (
    CollectionAddDocumentRequest,
    CollectionAddDocumentResponse,
    CollectionCreateRequest,
    CollectionCreateResponse,
    CollectionDocument,
    CollectionWithDocuments,
    
)
from apps.core.security import has_document_access
from database.managers.audit_manager import AuditManager
from database.managers.document_manager import DocumentManager
from database.managers.workspace_manager import WorkspaceManager


router = APIRouter(prefix="/collections", tags=["collections"])


@router.post(
    "",
    response_model=CollectionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_collection(
    payload: CollectionCreateRequest,
    user=Depends(get_current_user),
    workspace_manager: WorkspaceManager = Depends(get_workspace_manager),
    audit_manager: AuditManager = Depends(get_audit_manager),
):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Collection name cannot be empty")

    collection = await workspace_manager.create_collection(
        user_id=user.id,
        name=payload.name.strip(),
    )

    await audit_manager.log_event(
        user_id=user.id,
        action="create_collection",
        entity_type="workspace_collection",
        entity_id=str(collection.id),
        meta={"name": collection.name},
    )

    return CollectionCreateResponse(
        id=collection.id,
        name=collection.name,
        created_at=collection.created_at,
    )


@router.get(
    "",
    response_model=List[CollectionWithDocuments],
)
async def list_collections_with_documents(
    user=Depends(get_current_user),
    workspace_manager: WorkspaceManager = Depends(get_workspace_manager),
    document_manager: DocumentManager = Depends(get_document_manager),
):
    collections = await workspace_manager.list_collections_for_user(user.id)
    if not collections:
        return []

    collection_docs_map: Dict[UUID, List[UUID]] = {}
    all_doc_ids: set[UUID] = set()

    for col in collections:
        items = await workspace_manager.list_items_for_collection(col.id)
        doc_ids = [item.document_id for item in items]
        collection_docs_map[col.id] = doc_ids
        all_doc_ids.update(doc_ids)

    if not all_doc_ids:
        return [
            CollectionWithDocuments(
                id=col.id,
                name=col.name,
                created_at=col.created_at,
                documents_count=0,
                documents=[],
            )
            for col in collections
        ]

    documents = await document_manager.get_documents_by_ids(all_doc_ids)
    docs_by_id = {doc.id: doc for doc in documents}

    result: List[CollectionWithDocuments] = []

    for col in collections:
        docs_for_collection: List[CollectionDocument] = []

        for doc_id in collection_docs_map.get(col.id, []):
            doc = docs_by_id.get(doc_id)
            if doc is None:
                continue

            docs_for_collection.append(
                CollectionDocument(
                    document_id=doc.id,
                    title=doc.title,
                    department_id=doc.department_id,
                    access_levels=doc.access_levels,
                    tags=doc.tags,
                    is_actual=doc.is_valid,
                    upload_date=doc.upload_date,
                )
            )

        result.append(
            CollectionWithDocuments(
                id=col.id,
                name=col.name,
                created_at=col.created_at,
                documents_count=len(docs_for_collection),
                documents=docs_for_collection,
            )
        )

    return result


@router.post(
    "/{collection_id}/items",
    response_model=CollectionAddDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_document_to_collection(
    collection_id: str,
    payload: CollectionAddDocumentRequest,
    user=Depends(get_current_user),
    workspace_manager: WorkspaceManager = Depends(get_workspace_manager),
    document_manager: DocumentManager = Depends(get_document_manager),
):
    try:
        col_uuid = UUID(collection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid collection id")

    collection = await workspace_manager.get_collection_by_id(col_uuid)
    if collection is None or collection.user_id != user.id:
        raise HTTPException(status_code=404, detail="Collection not found")

    document = await document_manager.get_document_by_id(payload.document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if not has_document_access(user.access_levels, document.access_levels):
        raise HTTPException(status_code=404, detail="Document not found")

    item = await workspace_manager.add_document_to_collection(
        collection_id=col_uuid,
        document_id=document.id,
    )

    return CollectionAddDocumentResponse(
        collection_id=item.collection_id,
        document_id=item.document_id,
        created_at=item.created_at,
    )

