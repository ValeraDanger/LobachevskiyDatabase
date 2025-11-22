from dataclasses import dataclass
from typing import Optional

from database.models.document_metadata import DocumentMetadataVersion
from database.models.document_version import DocumentVersion

@dataclass
class DocumentVersionWithMetadata:
    version: DocumentVersion
    metadata: Optional[DocumentMetadataVersion]
