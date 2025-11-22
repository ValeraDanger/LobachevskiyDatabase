import os
from typing import Dict, Iterable, List, Optional, Tuple
from uuid import UUID

from apps.api.schemas.document_version import DocumentVersionWithMetadata
from database.async_db import AsyncDatabase
from database.managers.base import BaseManager
from database.models.document import Document
from database.models.document_version import DocumentVersion
from database.models.document_metadata import DocumentMetadataVersion


class DocumentManager(BaseManager):
    def __init__(self, db: AsyncDatabase) -> None:
        super().__init__(db)

    async def get_document_by_id(self, document_id: UUID) -> Optional[Document]:
        row = await self.db.fetchrow(
            "SELECT * FROM documents WHERE id = $1", document_id
        )
        return Document.from_record(row) if row else None

    async def get_versions_for_document(
        self, document_id: UUID
    ) -> List[DocumentVersionWithMetadata]:
        query = """
            SELECT
                dv.id              AS dv_id,
                dv.document_id     AS dv_document_id,
                dv.version         AS dv_version,
                dv.file_name       AS dv_file_name,
                dv.file_type       AS dv_file_type,
                dv.file_size       AS dv_file_size,
                dv.storage_key     AS dv_storage_key,
                dv.upload_date     AS dv_upload_date,
                dv.uploaded_by_id  AS dv_uploaded_by_id,
                dv.status          AS dv_status,
                dv.valid_from      AS dv_valid_from,
                dv.valid_to        AS dv_valid_to,
                dv.change_notes    AS dv_change_notes,
                dv.metadata        AS dv_metadata,
                dv.is_current      AS dv_is_current,

                dmv.document_version_id AS dmv_document_version_id,
                dmv.changed_at          AS dmv_changed_at,
                dmv.changed_by_id       AS dmv_changed_by_id,
                dmv.title               AS dmv_title,
                dmv.description         AS dmv_description,
                dmv.category            AS dmv_category,
                dmv.department_id       AS dmv_department_id,
                dmv.access_levels       AS dmv_access_levels,
                dmv.tags                AS dmv_tags,
                dmv.is_valid            AS dmv_is_valid,
                dmv.metadata            AS dmv_metadata
            FROM document_versions dv
            LEFT JOIN document_metadata_versions dmv
                ON dmv.document_version_id = dv.id
            WHERE dv.document_id = $1
            ORDER BY dv.version DESC
        """

        rows = await self.db.fetch(query, document_id)

        result: List[DocumentVersionWithMetadata] = []

        for row in rows:
            dv = DocumentVersion(
                id=row["dv_id"],
                document_id=row["dv_document_id"],
                version=row["dv_version"],
                file_name=row["dv_file_name"],
                file_type=row["dv_file_type"],
                file_size=row["dv_file_size"],
                storage_key=row["dv_storage_key"],
                upload_date=row["dv_upload_date"],
                uploaded_by_id=row["dv_uploaded_by_id"],
                status=row["dv_status"],
                valid_from=row["dv_valid_from"],
                valid_to=row["dv_valid_to"],
                change_notes=row["dv_change_notes"],
                metadata=row["dv_metadata"],
                is_current=row["dv_is_current"],
            )

            # metadata может быть NULL
            if row["dmv_document_version_id"] is None:
                dmv = None
            else:
                dmv = DocumentMetadataVersion(
                    document_version_id=row["dmv_document_version_id"],
                    changed_at=row["dmv_changed_at"],
                    changed_by_id=row["dmv_changed_by_id"],
                    title=row["dmv_title"],
                    description=row["dmv_description"],
                    category=row["dmv_category"],
                    department_id=row["dmv_department_id"],
                    access_levels=row["dmv_access_levels"],
                    tags=row["dmv_tags"],
                    is_valid=row["dmv_is_valid"],
                    metadata=row["dmv_metadata"],
                )

            result.append(DocumentVersionWithMetadata(version=dv, metadata=dmv))

        return result

    async def get_current_version(self, document_id: UUID) -> Optional[DocumentVersion]:
        query = """
            SELECT *
            FROM document_versions
            WHERE document_id = $1 AND is_current = true
            LIMIT 1
        """
        row = await self.db.fetchrow(query, document_id)
        return DocumentVersion.from_record(row) if row else None

    async def get_current_versions_for_documents(
        self,
        document_ids: Iterable[UUID],
    ) -> Dict[UUID, DocumentVersion]:
        ids_list = list(document_ids)
        if not ids_list:
            return {}

        rows = await self.db.fetch(
            """
            SELECT *
            FROM document_versions
            WHERE document_id = ANY($1::uuid[])
              AND is_current = true
            """,
            ids_list,
        )
        return {r["document_id"]: DocumentVersion.from_record(r) for r in rows}

    async def create_document_with_version(
        self,
        *,
        title: str,
        department_id: int,
        uploaded_by_id: UUID,
        file_name: str,
        file_type: str,
        file_size: int,
        storage_key: str,
        tags: List[str],
    ) -> Tuple[Document, DocumentVersion]:
        """
        Создаёт документ + первую версию
        """
        doc_row = await self.db.fetchrow(
            """
            INSERT INTO documents (
                title,
                department_id,
                access_levels,
                tags,
                uploaded_by_id,
                status,
                is_valid,
                current_version
            )
            VALUES ($1, $2, '{}', $3, $4, 'draft', true, 1)
            RETURNING *
            """,
            title,
            department_id,
            tags,
            uploaded_by_id,
        )
        if doc_row is None:
            raise RuntimeError("Failed to create document")
        document = Document.from_record(doc_row)

        ver_row = await self.db.fetchrow(
            """
            INSERT INTO document_versions (
                document_id,
                version,
                file_name,
                file_type,
                file_size,
                storage_key,
                uploaded_by_id,
                status,
                is_current
            )
            VALUES ($1, 1, $2, $3, $4, $5, $6, 'draft', true)
            RETURNING *
            """,
            document.id,
            file_name,
            file_type,
            file_size,
            storage_key,
            uploaded_by_id,
        )
        if ver_row is None:
            raise RuntimeError("Failed to create document version")
        version = DocumentVersion.from_record(ver_row)

        await self.db.execute(
            """
                INSERT INTO document_metadata_versions (
                    document_version_id,
                    changed_by_id,
                    title,
                    description,
                    category,
                    department_id,
                    access_levels,
                    tags,
                    is_valid,
                    metadata
                )
                VALUES ($1, $2, $3, NULL, NULL, $4, '{}', $5, true, NULL)
                """,
            version.id,
            uploaded_by_id,
            title,
            department_id,
            tags,
        )

        return document, version

    async def get_document_with_current_version(
        self, document_id: UUID
    ) -> Tuple[Document, Optional[DocumentVersion]]:
        doc_row = await self.db.fetchrow(
            "SELECT * FROM documents WHERE id = $1",
            document_id,
        )
        if doc_row is None:
            raise RuntimeError("Document not found")
        document = Document.from_record(doc_row)

        ver_row = await self.db.fetchrow(
            """
            SELECT *
            FROM document_versions
            WHERE document_id = $1 AND is_current = true
            """,
            document_id,
        )
        version = DocumentVersion.from_record(ver_row) if ver_row else None
        return document, version

    async def update_document_main_fields(
        self,
        document_id: UUID,
        *,
        title: str,
        department_id: int,
        access_levels: list[str],
        tags: list[str],
        status: Optional[str] = None,
        is_valid: Optional[bool] = None,
    ) -> Document:
        query = """
        UPDATE documents
        SET
            title = $2,
            department_id = $3,
            access_levels = $4,
            last_modified = now(),
            tags = $5,
            status = COALESCE($6, status),
            is_valid = COALESCE($7, is_valid)
        WHERE id = $1
        RETURNING *
        """
        row = await self.db.fetchrow(
            query,
            document_id,
            title,
            department_id,
            access_levels,
            tags,
            status,
            is_valid,
        )
        if row is None:
            raise RuntimeError("Failed to update document")
        return Document.from_record(row)

    async def update_current_version_status(
        self,
        document_id: UUID,
        *,
        new_status: str,
    ) -> DocumentVersion:
        row = await self.db.fetchrow(
            """
            UPDATE document_versions
            SET status = $2
            WHERE document_id = $1 AND is_current = true
            RETURNING *
            """,
            document_id,
            new_status,
        )
        if row is None:
            raise RuntimeError("Failed to update document version status")
        return DocumentVersion.from_record(row)

    async def get_documents_by_ids(
        self,
        ids: Iterable[UUID],
    ) -> List[Document]:
        ids_list = list(ids)
        if not ids_list:
            return []

        query = """
        SELECT *
        FROM documents
        WHERE id = ANY($1::uuid[])
        """
        rows = await self.db.fetch(query, ids_list)
        return [Document(**dict(r)) for r in rows]

    async def create_new_version_and_update_document(
        self,
        document_id: UUID,
        *,
        title: str,
        department_id: int | None,
        access_levels: list[str],
        tags: list[str],
        status: Optional[str] = None,
        is_valid: Optional[bool] = None,
        uploaded_by_id: UUID,
        file_name: Optional[str] = None,
        file_type: Optional[str] = None,
        file_size: Optional[int] = None,
        storage_key: Optional[str] = None,
        change_notes: Optional[str] = None,
        version_status: Optional[str] = None,
    ) -> Tuple[Document, DocumentVersion]:
        """
        Создаёт новую версию документа (document_versions + document_metadata_versions)
        и обновляет основную запись в documents.
        """
        document, current_ver = await self.get_document_with_current_version(
            document_id
        )
        if current_ver is None:
            raise RuntimeError("Current document version not found")

        base_version = current_ver.version or document.current_version or 0
        new_version_num = base_version + 1

        new_file_name = file_name or current_ver.file_name
        new_file_type = file_type or current_ver.file_type
        new_file_size = file_size or current_ver.file_size
        new_storage_key = storage_key or current_ver.storage_key

        if file_type is not None and file_type != current_ver.file_type:
            raise RuntimeError("Changing file type is not allowed")

        new_department_id = (
            department_id if department_id is not None else document.department_id
        )
        new_status = status if status is not None else document.status
        new_is_valid = is_valid if is_valid is not None else document.is_valid
        new_access_levels = access_levels
        new_tags = tags
        new_title = title
        new_description = document.description
        new_category = document.category
        new_metadata = document.metadata

        new_version_status = version_status or current_ver.status

        await self.db.execute(
            """
            UPDATE document_versions
            SET is_current = false
            WHERE document_id = $1 AND is_current = true
            """,
            document_id,
        )

        ver_row = await self.db.fetchrow(
            """
            INSERT INTO document_versions (
                document_id,
                version,
                file_name,
                file_type,
                file_size,
                storage_key,
                uploaded_by_id,
                status,
                change_notes,
                is_current
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::doc_version_status, $9, true)
            RETURNING *
            """,
            document_id,
            new_version_num,
            new_file_name,
            new_file_type,
            new_file_size,
            new_storage_key,
            uploaded_by_id,
            new_version_status,
            change_notes,
        )
        if ver_row is None:
            raise RuntimeError("Failed to create new document version")
        new_version = DocumentVersion.from_record(ver_row)
        await self.db.execute(
            """
            INSERT INTO document_metadata_versions (
                document_version_id,
                changed_by_id,
                title,
                description,
                category,
                department_id,
                access_levels,
                tags,
                is_valid,
                metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
            new_version.id,
            uploaded_by_id,
            new_title,
            new_description,
            new_category,
            new_department_id,
            new_access_levels,
            new_tags,
            new_is_valid,
            new_metadata,
        )

        doc_row = await self.db.fetchrow(
            """
            UPDATE documents
            SET
                title = $2,
                department_id = $3,
                access_levels = $4,
                tags = $5,
                status = $6,
                is_valid = $7,
                current_version = $8,
                last_modified = now()
            WHERE id = $1
            RETURNING *
            """,
            document_id,
            new_title,
            new_department_id,
            new_access_levels,
            new_tags,
            new_status,
            new_is_valid,
            new_version_num,
        )
        if doc_row is None:
            raise RuntimeError("Failed to update document")
        updated_doc = Document.from_record(doc_row)

        return updated_doc, new_version

    async def get_document_ids_by_storage_keys(
        self,
        storage_keys: Iterable[str],
    ) -> Dict[str, UUID]:
        keys_list = list(storage_keys)
        if not keys_list:
            return {}

        rows = await self.db.fetch(
            """
            SELECT storage_key, document_id
            FROM document_versions
            WHERE storage_key = ANY($1::text[])
            """,
            keys_list,
        )
        return {r["storage_key"]: r["document_id"] for r in rows}
    
    async def get_all_file_types(self) -> list[str]:
        rows = await self.db.fetch(
            """
            SELECT DISTINCT file_type
            FROM document_versions
            WHERE file_type IS NOT NULL AND file_type <> ''
            ORDER BY file_type
            """
        )
        return [r["file_type"] for r in rows]


