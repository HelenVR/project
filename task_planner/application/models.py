from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from typing import Optional
from pydantic import BaseModel

Base = declarative_base()


class Task(Base):
    __tablename__ = 'tasks_data'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    deadline = Column(DateTime)
    comment = Column(Text)
    done = Column(Boolean, default=False)

    def __repr__(self):
        return f"Название: {self.name}\nКомментарий: {self.comment}\nВыполнить до: {self.deadline.strftime('%Y-%m-%d')}"


class SearchTaskRequest(BaseModel):
    name: Optional[str] = None
    comment: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    done: Optional[str] = None

