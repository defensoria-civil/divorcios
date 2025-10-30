from sqlalchemy.orm import Session
from typing import Optional, List
from .models import Case, Message, Memory

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
