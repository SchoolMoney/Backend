from datetime import date
from pydantic import BaseModel

class CollectionOperationMetadata(BaseModel):
    collection_id: int
    
    child_id: int
    child_name: str
    child_surname: str
    
    requestor_id: int
    requestor_name: str
    requestor_surname: str
    
    operation_date: date
    operation_type: int
