"""
Endpoints de Gestión de Usuarios.

Solo accesibles para administradores.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List

from infrastructure.persistence.db import get_db
from infrastructure.persistence.repositories import UserRepository
from presentation.api.dependencies.security import get_current_operator

router = APIRouter()


# ==================== Request/Response Models ====================

class CreateUserRequest(BaseModel):
    """Request para crear un nuevo usuario"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "operator"  # operator | admin


class UpdateUserRequest(BaseModel):
    """Request para actualizar un usuario"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    """Request para cambiar contraseña"""
    new_password: str


class UserResponse(BaseModel):
    """Response con datos de usuario"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


# ==================== Dependency ====================

def require_admin(current_user: dict = Depends(get_current_operator)):
    """Verifica que el usuario actual sea admin"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador"
        )
    return current_user


# ==================== Endpoints ====================

@router.get("/", response_model=List[UserResponse])
def list_users(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    Lista todos los usuarios del sistema.
    
    **Requiere:** Rol de administrador
    
    **Query params:**
    - include_inactive: Si True, incluye usuarios inactivos (default: False)
    """
    user_repo = UserRepository(db)
    users = user_repo.list_all(include_inactive=include_inactive)
    
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else ""
        )
        for user in users
    ]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    Obtiene información detallada de un usuario.
    
    **Requiere:** Rol de administrador
    """
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else ""
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: CreateUserRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    Crea un nuevo usuario.
    
    **Requiere:** Rol de administrador
    
    **Validaciones:**
    - Username único
    - Email único
    - Password mínimo 6 caracteres
    - Role válido (operator o admin)
    """
    user_repo = UserRepository(db)
    
    # Validar que username no exista
    if user_repo.get_by_username(data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El username ya está en uso"
        )
    
    # Validar que email no exista
    if user_repo.get_by_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Validar longitud de password
    if len(data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 6 caracteres"
        )
    
    # Validar role
    if data.role not in ["operator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rol debe ser 'operator' o 'admin'"
        )
    
    # Crear usuario
    user = user_repo.create_user(
        username=data.username,
        email=data.email,
        password=data.password,
        full_name=data.full_name,
        role=data.role
    )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else ""
    )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UpdateUserRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    Actualiza información de un usuario.
    
    **Requiere:** Rol de administrador
    
    **Nota:** No se puede cambiar el username
    """
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Prevenir que un admin se quite sus propios permisos
    if user.id == current_user.get("user_id") and data.role and data.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes cambiar tu propio rol de administrador"
        )
    
    # Actualizar campos
    if data.email is not None:
        # Verificar que el email no esté en uso
        existing = user_repo.get_by_email(data.email)
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso"
            )
        user.email = data.email
    
    if data.full_name is not None:
        user.full_name = data.full_name
    
    if data.role is not None:
        if data.role not in ["operator", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El rol debe ser 'operator' o 'admin'"
            )
        user.role = data.role
    
    if data.is_active is not None:
        # Prevenir que un admin se desactive a sí mismo
        if user.id == current_user.get("user_id") and not data.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes desactivar tu propia cuenta"
            )
        user.is_active = data.is_active
    
    updated_user = user_repo.update_user(user)
    
    return UserResponse(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        full_name=updated_user.full_name,
        role=updated_user.role,
        is_active=updated_user.is_active,
        created_at=updated_user.created_at.isoformat() if updated_user.created_at else ""
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    Elimina un usuario del sistema.
    
    **Requiere:** Rol de administrador
    
    **Nota:** No se puede eliminar el propio usuario
    """
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Prevenir que un admin se elimine a sí mismo
    if user.id == current_user.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta"
        )
    
    user_repo.delete_user(user_id)
    return None


@router.post("/{user_id}/change-password", status_code=status.HTTP_200_OK)
def change_user_password(
    user_id: int,
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """
    Cambia la contraseña de un usuario.
    
    **Requiere:** Rol de administrador
    """
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Validar longitud de password
    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 6 caracteres"
        )
    
    # Actualizar contraseña
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user.hashed_password = pwd_context.hash(data.new_password)
    
    user_repo.update_user(user)
    
    return {"message": "Contraseña actualizada correctamente"}
