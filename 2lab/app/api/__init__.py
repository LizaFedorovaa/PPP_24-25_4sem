from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse, UserMeResponse, EncodeRequest, EncodeResponse, DecodeRequest, DecodeResponse
from app.cruds.user import create_user
from app.services.security import verify_password, create_access_token, get_current_user, oauth2_scheme
from app.services.encoding import encode_data, decode_data
from app.db import get_db
from datetime import timedelta
from app.core.config import settings
from app.models.user import User

auth_router = APIRouter()

@auth_router.post("/sign-up/", response_model=UserResponse)
def sign_up(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = create_user(db, email=user.email, password=user.password)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    return UserResponse(id=new_user.id, email=new_user.email, token=access_token)

@auth_router.post("/login/", response_model=dict)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == form_data.username).first()
    if not u or not verify_password(form_data.password, u.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    tkn = create_access_token(
        data={"sub": u.email},
        expires_delta=access_token_expires
    )
    return {
        "access_token": tkn,
        "id": u.id,
        "email": u.email
    }

@auth_router.get("/users/me/", response_model=UserMeResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@auth_router.post("/encode", response_model=EncodeResponse)
def encode(request: EncodeRequest):
    encoded_data, huffman_codes, padding = encode_data(request.text, request.key)
    return EncodeResponse(
        encoded_data=encoded_data,
        key=request.key,
        huffman_codes=huffman_codes,
        padding=padding
    )

@auth_router.post("/decode", response_model=DecodeResponse)
def decode(request: DecodeRequest):
    try:
        decoded_text = decode_data(request.encoded_data, request.key, request.huffman_codes, request.padding)
        return DecodeResponse(decoded_text=decoded_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decoding failed: {str(e)}")