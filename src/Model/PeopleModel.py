from fastapi import HTTPException, status

from pydantic import BaseModel

class ParentModel(BaseModel):
    name: str
    surname: str
    phone: str
    city: str
    street: str
    house_number: str

    def is_valid_number(self) -> None:
        if self.phone and ((self.phone.startswith('+') and self.phone[1:].isalnum()) or self.phone.isdigit()):
            return None
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect phone number",
        )
