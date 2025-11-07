"""
Endpoints de Autenticación.

Proporciona rutas para:
- Login de usuarios
- Registro de nuevos usuarios
- Obtención de usuario actual
- Refresh de tokens
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.persistence.db import get_db
from infrastructure.persistence.repositories import UserRepository
from application.use_cases.authenticate_user import (
    AuthenticateUserUseCase,
    LoginRequest,
    LoginResponse
)
from presentation.api.dependencies.security import get_current_operator, security


router = APIRouter()


# ==================== Request/Response Models ====================

class LoginRequestModel(BaseModel):
    """Modelo de request para login"""
    username: str
    password: str


class RegisterRequestModel(BaseModel):
    """Modelo de request para registro"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserResponseModel(BaseModel):
    """Modelo de response con datos de usuario"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str


class RefreshTokenRequest(BaseModel):
    """Request para refresh de token"""
    token: str


# ==================== Endpoints ====================

@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    credentials: LoginRequestModel,
    db: Session = Depends(get_db)
):
    """
    Autenticar usuario y generar token JWT.
    
    **Flujo:**
    1. Valida username y password
    2. Genera JWT con role del usuario
    3. Retorna token y datos del usuario
    
    **Errores:**
    - 401: Credenciales inválidas
    - 403: Usuario desactivado
    """
    use_case = AuthenticateUserUseCase(db)
    
    login_request = LoginRequest(
        username=credentials.username,
        password=credentials.password
    )
    
    response = use_case.execute(login_request)
    
    return response


@router.post("/register", response_model=UserResponseModel, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequestModel,
    db: Session = Depends(get_db)
):
    """
    Registrar un nuevo usuario.
    
    **Validaciones:**
    - Username único
    - Email único
    - Password mínimo 6 caracteres
    
    **Nota:** Los usuarios registrados tienen rol 'operator' por defecto.
    Solo admins pueden crear otros admins.
    
    **Errores:**
    - 400: Username o email ya existen
    - 422: Datos inválidos
    """
    users_repo = UserRepository(db)
    
    # Validar que username no exista
    existing_user = users_repo.get_by_username(data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El username ya está en uso"
        )
    
    # Validar que email no exista
    existing_email = users_repo.get_by_email(data.email)
    if existing_email:
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
    
    # Crear usuario
    user = users_repo.create_user(
        username=data.username,
        email=data.email,
        password=data.password,
        full_name=data.full_name,
        role="operator"  # Por defecto operator
    )
    
    return UserResponseModel(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role
    )


@router.get("/me", response_model=dict, status_code=status.HTTP_200_OK)
async def get_current_user(
    current_user: dict = Depends(get_current_operator),
    db: Session = Depends(get_db)
):
    """
    Obtener información del usuario actual.
    
    **Requiere:** Token JWT válido en header Authorization
    
    **Retorna:** Datos completos del usuario autenticado
    
    **Errores:**
    - 401: Token inválido o expirado
    - 404: Usuario no encontrado
    """
    username = current_user.get("sub")
    
    users_repo = UserRepository(db)
    user = users_repo.get_by_username(username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.post("/refresh", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    current_user: dict = Depends(get_current_operator),
    db: Session = Depends(get_db)
):
    """
    Renovar token JWT.
    
    **Requiere:** Token JWT válido (aunque esté próximo a expirar)
    
    **Retorna:** Nuevo token con tiempo de expiración renovado
    
    **Errores:**
    - 401: Token inválido
    - 404: Usuario no encontrado
    """
    username = current_user.get("sub")
    
    users_repo = UserRepository(db)
    user = users_repo.get_by_username(username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )
    
    # Generar nuevo token usando el use case
    use_case = AuthenticateUserUseCase(db)
    access_token = use_case._create_access_token(
        data={"sub": user.username, "role": user.role, "user_id": user.id}
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: dict = Depends(get_current_operator)):
    """
    Logout del usuario.
    
    **Nota:** En JWT stateless, el logout es manejado por el cliente
    eliminando el token. Este endpoint existe para consistencia de API.
    
    Para invalidación real de tokens, se requeriría:
    - Blacklist de tokens en Redis
    - O reducir tiempo de expiración de tokens
    """
    return {"message": "Logout exitoso. Elimine el token del cliente."}
