from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.schemas.token import TokenCreate, TokenResponse, TokenUpdate, TokenCreateResponse
from app.models.token import Token, TokenRole
from app.models.user import User, UserRole
from app.dependencies.auth import get_current_user, require_role
from app.services.auth import AuthService

router = APIRouter(prefix="/tokens", tags=["tokens"])


@router.get("", response_model=List[TokenResponse])
async def list_tokens(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Lista todos os tokens (apenas admin)"""
    query = db.query(Token)

    # Busca por nome
    if search:
        search_term = f"%{search}%"
        query = query.filter(Token.name.ilike(search_term))

    tokens = query.order_by(Token.created_at.desc()).offset(skip).limit(limit).all()
    return tokens


@router.get("/{token_uuid}", response_model=TokenResponse)
async def get_token(
    token_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Busca um token por UUID (apenas admin)"""
    token = db.query(Token).filter(Token.uuid == token_uuid).first()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token não encontrado"
        )
    return token


@router.post("", response_model=TokenCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_token(
    token_data: TokenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Cria um novo token (apenas admin)"""
    # Gerar token aleatório
    plain_token = AuthService.generate_token()
    token_hash = AuthService.hash_token(plain_token)

    # Criar token no banco
    new_token = Token(
        name=token_data.name,
        token_hash=token_hash,
        role=token_data.role,
        expires_at=token_data.expires_at,
        user_id=current_user.id if hasattr(current_user, 'id') else None
    )
    db.add(new_token)
    db.commit()
    db.refresh(new_token)

    # Retornar resposta com o token em texto plano (só aparece na criação)
    return {
        "uuid": str(new_token.uuid),
        "name": new_token.name,
        "token": plain_token,  # Token em texto plano - só aparece aqui
        "role": new_token.role,
        "expires_at": new_token.expires_at.isoformat() if new_token.expires_at else None,
        "created_at": new_token.created_at.isoformat()
    }


@router.put("/{token_uuid}", response_model=TokenResponse)
async def update_token(
    token_uuid: str,
    token_data: TokenUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Atualiza um token (apenas admin)"""
    token = db.query(Token).filter(Token.uuid == token_uuid).first()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token não encontrado"
        )

    # Atualizar campos
    if token_data.name is not None:
        token.name = token_data.name

    if token_data.role is not None:
        token.role = token_data.role

    if token_data.is_active is not None:
        token.is_active = token_data.is_active

    if token_data.expires_at is not None:
        token.expires_at = token_data.expires_at

    db.commit()
    db.refresh(token)

    return token


@router.delete("/{token_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_token(
    token_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Deleta um token (apenas admin)"""
    token = db.query(Token).filter(Token.uuid == token_uuid).first()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token não encontrado"
        )

    db.delete(token)
    db.commit()

    return None

