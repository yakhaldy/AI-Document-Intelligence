from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.models import User
from src.api.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_user_by_username,
    hash_password,
)
from src.api.deps import get_db
from src.api.schemas import LoginRequest, RegisterRequest, RegisterResponse, Token, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, session: Session = Depends(get_db)):
    user = authenticate_user(session, payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides, ou compte pas encore approuvé par un administrateur",
        )
    return Token(access_token=create_access_token(user.username))


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        422: {"description": "Nom d'utilisateur ou mot de passe trop court"},
        409: {"description": "Nom d'utilisateur déjà pris"},
    },
)
def register(payload: RegisterRequest, session: Session = Depends(get_db)):
    username = payload.username.strip()
    if len(username) < 3 or len(payload.password) < 8:
        raise HTTPException(
            status_code=422,
            detail="Nom d'utilisateur ≥ 3 caractères, mot de passe ≥ 8 caractères",
        )
    if get_user_by_username(session, username) is not None:
        raise HTTPException(status_code=409, detail="Ce nom d'utilisateur existe déjà")

    user = User(username=username, password_hash=hash_password(payload.password), role="user", status="pending")
    session.add(user)
    session.commit()
    return RegisterResponse(message="Compte créé, en attente d'approbation par un administrateur")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut(id=user.id, username=user.username, role=user.role, status=user.status)
