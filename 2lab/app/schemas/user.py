from pydantic import BaseModel
from typing import Dict

class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    token: str

    class Config:
        from_attributes = True

class UserMeResponse(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True

class EncodeRequest(BaseModel):
    text: str
    key: str

class EncodeResponse(BaseModel):
    encoded_data: str
    key: str
    huffman_codes: Dict[str, str]
    padding: int

class DecodeRequest(BaseModel):
    encoded_data: str
    key: str
    huffman_codes: Dict[str, str]
    padding: int

class DecodeResponse(BaseModel):
    decoded_text: str