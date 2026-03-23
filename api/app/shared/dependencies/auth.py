from fastapi import Depends, HTTPException, Request, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Union
from datetime import datetime, timezone
from uuid import uuid4
from app.shared.database.database import get_db
from app.users.infra.user_model import User, UserRole
from app.auth.infra.token_model import Token
from app.users.infra.user_repository import UserRepository
from app.auth.infra.token_repository import TokenRepository
from app.auth.core.auth_service import AuthService

security = HTTPBearer(auto_error=False)


async def get_current_user_or_token(
    request: Request,
    x_tron_token: Optional[str] = Header(None, alias="x-tron-token"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Union[User, Token]:
    """
    Valida autenticação via JWT (Bearer token) ou x-tron-token.
    Retorna User ou Token dependendo do método de autenticação.
    """
    user_repository = UserRepository(db)
    token_repository = TokenRepository(db)
    auth_service = AuthService(user_repository, token_repository)

    # Priority: x-tron-token first
    if x_tron_token:
        token = auth_service.get_token_by_hash(x_tron_token)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
            )

        if not token.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inativo"
            )

        # Check expiration
        if token.expires_at and token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado"
            )

        request.state.audit_actor = f"token:{token.name}"
        return token

    # Fallback para JWT
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
        )

    jwt_token = credentials.credentials
    payload = auth_service.verify_token(jwt_token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Tipo de token inválido"
        )

    user_uuid = payload.get("sub")
    if not user_uuid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        )

    from uuid import UUID as UUIDType

    user = user_repository.find_by_uuid(UUIDType(user_uuid))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive"
        )

    request.state.audit_actor = user.email
    return user


# Classe auxiliar para simular User quando autenticado via Token
class TokenUser:
    """Classe simples que simula User para tokens de API"""

    def __init__(self, token: Token, db: Session):
        self.id = 0
        self.email = f"token_{token.uuid}"
        self.hashed_password = None
        self.full_name = token.name
        self.is_active = token.is_active
        self.google_id = None
        self.avatar_url = None
        self.created_at = token.created_at
        self.updated_at = token.updated_at
        self._token = token  # Store reference to original token

        # Get user info from associated user if exists
        if token.user_id:
            from app.users.infra.user_model import User as UserModel

            user = db.query(UserModel).filter(UserModel.id == token.user_id).first()
            if user:
                self.uuid = user.uuid
                self.id = user.id
                self.role = user.role
            else:
                self.uuid = uuid4()
                self.role = UserRole.USER.value
        else:
            self.uuid = uuid4()
            self.role = UserRole.USER.value


async def get_current_user(
    current_auth: Union[User, Token] = Depends(get_current_user_or_token),
    db: Session = Depends(get_db),
) -> Union[User, TokenUser]:
    """
    Extrai apenas User da autenticação.
    Se for Token, converte para um objeto User simulado com a role do usuário associado ao token.
    """
    if isinstance(current_auth, User):
        return current_auth

    # Se for Token, criar um objeto User simulado com a role do usuário associado
    # Se o token não tiver usuário associado, usa role padrão 'user'
    return TokenUser(current_auth, db)


def require_role(allowed_roles: list[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)):
        # Convert allowed_roles to values (strings) for comparison
        allowed_role_values = [
            role.value if isinstance(role, UserRole) else role for role in allowed_roles
        ]
        if current_user.role not in allowed_role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return current_user

    return role_checker
