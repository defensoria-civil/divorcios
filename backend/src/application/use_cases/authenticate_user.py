"""
Use Case de Autenticación de Usuarios.

Responsabilidades:
- Validar credenciales de usuario
- Generar JWT tokens con información del usuario
- Manejo de errores de autenticación
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from fastapi import HTTPException
from sqlalchemy.orm import Session
from infrastructure.persistence.repositories import UserRepository
from core.config import settings


@dataclass
class LoginRequest:
    """Request de login con credenciales"""
    username: str
    password: str


@dataclass
class LoginResponse:
    """Response exitoso de login con token"""
    access_token: str
    token_type: str
    user: dict


class AuthenticateUserUseCase:
    """
    Use Case para autenticar usuarios y generar tokens JWT.
    
    Flujo:
    1. Buscar usuario por username
    2. Verificar password con bcrypt
    3. Validar que usuario esté activo
    4. Generar JWT con datos del usuario (username, role)
    5. Retornar token y datos del usuario
    """
    
    def __init__(self, db: Session):
        self.users = UserRepository(db)
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24  # 24 horas
    
    def execute(self, request: LoginRequest) -> LoginResponse:
        """
        Ejecuta el proceso de autenticación.
        
        Args:
            request: Credenciales de login
        
        Returns:
            LoginResponse con token y datos del usuario
        
        Raises:
            HTTPException: Si las credenciales son inválidas o usuario inactivo
        """
        # 1. Buscar usuario
        user = self.users.get_by_username(request.username)
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Credenciales inválidas"
            )
        
        # 2. Verificar password
        if not self.users.verify_password(user, request.password):
            raise HTTPException(
                status_code=401,
                detail="Credenciales inválidas"
            )
        
        # 3. Verificar que usuario esté activo
        if not user.is_active:
            raise HTTPException(
                status_code=403,
                detail="Usuario desactivado. Contacte al administrador."
            )
        
        # 4. Generar JWT
        access_token = self._create_access_token(
            data={"sub": user.username, "role": user.role, "user_id": user.id}
        )
        
        # 5. Retornar response
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
    
    def _create_access_token(
        self, 
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Crea un JWT token.
        
        Args:
            data: Payload del token
            expires_delta: Tiempo de expiración personalizado
        
        Returns:
            Token JWT codificado
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        
        return encoded_jwt
