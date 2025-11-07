from sqlalchemy.orm import Session
from typing import Optional, List
from .models import Case, Message, Memory, User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_by_phone(self, phone: str) -> Case:
        case = self.db.query(Case).filter(Case.phone == phone).first()
        if not case:
            case = Case(phone=phone)
            self.db.add(case)
            self.db.commit()
            self.db.refresh(case)
        return case

    def update(self, case: Case):
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)

class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_message(self, case_id: int, role: str, content: str) -> Message:
        m = Message(case_id=case_id, role=role, content=content)
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return m

    def last_messages(self, case_id: int, limit: int = 10) -> List[Message]:
        return (
            self.db.query(Message)
            .filter(Message.case_id == case_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )

class MemoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_memory(self, case_id: int, kind: str, content: str):
        mem = Memory(case_id=case_id, kind=kind, content=content)
        self.db.add(mem)
        self.db.commit()
        self.db.refresh(mem)
        return mem

class UserRepository:
    """
    Repositorio para gestión de usuarios y autenticación.
    
    Responsabilidades:
    - CRUD de usuarios
    - Hashing de contraseñas con bcrypt
    - Verificación de credenciales
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Busca usuario por username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Busca usuario por email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Busca usuario por ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create_user(
        self, 
        username: str, 
        email: str, 
        password: str, 
        full_name: Optional[str] = None,
        role: str = "operator"
    ) -> User:
        """
        Crea un nuevo usuario con password hasheado.
        
        Args:
            username: Nombre de usuario único
            email: Email único
            password: Contraseña en texto plano (se hashea automáticamente)
            full_name: Nombre completo del usuario
            role: Rol del usuario (operator | admin)
        
        Returns:
            Usuario creado
        
        Raises:
            IntegrityError: Si username o email ya existen
        """
        # Hash password con passlib
        hashed_password = pwd_context.hash(password)
        
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def verify_password(self, user: User, password: str) -> bool:
        """
        Verifica si la contraseña es correcta.
        
        Args:
            user: Usuario a verificar
            password: Contraseña en texto plano
        
        Returns:
            True si la contraseña es correcta
        """
        return pwd_context.verify(password, user.hashed_password)
    
    def update_user(self, user: User) -> User:
        """Actualiza un usuario existente"""
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """Elimina un usuario por ID"""
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False
    
    def list_all(self, include_inactive: bool = False) -> List[User]:
        """Lista todos los usuarios"""
        query = self.db.query(User)
        if not include_inactive:
            query = query.filter(User.is_active == True)
        return query.all()
