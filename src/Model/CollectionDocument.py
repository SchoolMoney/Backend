from pydantic import BaseModel

class CollectionDocument(BaseModel):
    document_id: int | None = None
    collection_id: int
    document_name: str
    document_path: str

class CreateCollectionDocument(BaseModel):
    collection_id: int
    document_name: str
    document_path: str