import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import Token, UserCreate, UserResponse, LoginRequest, RefreshTokenRequest, UpdateProfileRequest
from app.services.auth import AuthService
from app.models.user import User, UserRole
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )

    access_token = AuthService.create_access_token(data={"sub": str(user.uuid)})
    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.uuid)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Endpoint alternativo para compatibilidade com OAuth2PasswordRequestForm"""
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )

    access_token = AuthService.create_access_token(data={"sub": str(user.uuid)})
    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.uuid)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    # Verificar se usuário já existe
    existing_user = AuthService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )

    # Criar novo usuário
    hashed_password = AuthService.get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=UserRole.USER.value  # Usar .value pois agora é string
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    payload = AuthService.verify_token(token_data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    user_uuid = payload.get("sub")
    user = AuthService.get_user_by_uuid(db, user_uuid)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo"
        )

    access_token = AuthService.create_access_token(data={"sub": str(user.uuid)})
    refresh_token = AuthService.create_refresh_token(data={"sub": str(user.uuid)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    profile_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza o perfil do usuário atual"""
    # Se está tentando mudar o email, verificar se já existe
    if profile_data.email and profile_data.email != current_user.email:
        existing_user = AuthService.get_user_by_email(db, profile_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado"
            )
        current_user.email = profile_data.email

    # Se está tentando mudar a senha, verificar senha atual
    if profile_data.password:
        if not profile_data.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Senha atual é necessária para alterar a senha"
            )

        # Verificar senha atual
        if not AuthService.verify_password(profile_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Senha atual incorreta"
            )

        # Atualizar senha
        current_user.hashed_password = AuthService.get_password_hash(profile_data.password)

    # Atualizar nome se fornecido
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name

    db.commit()
    db.refresh(current_user)

    return current_user


# OAuth com Google (será implementado quando necessário)
@router.get("/google/login")
async def google_login():
    """Endpoint para iniciar login com Google"""
    # Será implementado quando configurar OAuth
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Login com Google será implementado em breve"
    )

