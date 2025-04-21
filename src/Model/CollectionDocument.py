from pydantic import BaseModel
from typing import Optional

class CollectionDocument(BaseModel):
    document_id: Optional[int] = None
    collection_id: int
    document_name: str
    file_type: str
    file_data: bytes

class CreateCollectionDocument(BaseModel):
    collection_id: int
    document_name: str
    file_type: str
    file_data: str

class CreateCollectionDocumentDB(BaseModel):
    collection_id: int
    document_name: str
    file_type: str
    file_data: bytes

class CollectionDocumentMetadata(BaseModel):
    document_id: Optional[int] = None
    collection_id: int
    document_name: str
    file_type: str