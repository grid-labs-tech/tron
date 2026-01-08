from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Union
from datetime import datetime
from uuid import uuid4
from app.database import get_db
from app.models.user import User, UserRole
from app.models.token import Token
from app.services.auth import AuthService

security = HTTPBearer(auto_error=False)


async def get_current_user_or_token(
    x_tron_token: Optional[str] = Header(None, alias="x-tron-token"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Union[User, Token]:
    """
    Valida autenticação via JWT (Bearer token) ou x-tron-token.
    Retorna User ou Token dependendo do método de autenticação.
    """
    # Prioridade: x-tron-token primeiro
    if x_tron_token:
        token = AuthService.get_token_by_hash(db, x_tron_token)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )

        if not token.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inativo"
            )

        # Verificar expiração
        if token.expires_at and token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado"
            )

        return token

    # Fallback para JWT
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido"
        )

    jwt_token = credentials.credentials
    payload = AuthService.verify_token(jwt_token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido"
        )

    user_uuid = payload.get("sub")
    if not user_uuid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    user = db.query(User).filter(User.uuid == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo"
        )

    return user


# Classe auxiliar para simular User quando autenticado via Token
class TokenUser:
    """Classe simples que simula User para tokens de API"""
    def __init__(self, token: Token):
        self.id = 0
        self.uuid = uuid4()
        self.email = f"token_{token.uuid}"
        self.hashed_password = None
        self.full_name = token.name
        self.is_active = token.is_active
        self.role = token.role
        self.google_id = None
        self.avatar_url = None
        self.created_at = token.created_at
        self.updated_at = token.updated_at


async def get_current_user(
    current_auth: Union[User, Token] = Depends(get_current_user_or_token)
) -> Union[User, TokenUser]:
    """
    Extrai apenas User da autenticação.
    Se for Token, converte para um objeto User simulado com a role do token.
    """
    if isinstance(current_auth, User):
        return current_auth

    # Se for Token, criar um objeto User simulado com a role do token
    # Isso permite que tokens funcionem com o sistema de roles existente
    return TokenUser(current_auth)


def require_role(allowed_roles: list[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)):
        # Converter allowed_roles para valores (strings) para comparação
        allowed_role_values = [role.value if isinstance(role, UserRole) else role for role in allowed_roles]
        if current_user.role not in allowed_role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão insuficiente"
            )
        return current_user
    return role_checker

