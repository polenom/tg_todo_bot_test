import enum
from sqlalchemy import Integer, Column, ForeignKey, String, Enum, Boolean, text, MetaData

from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from main.variables import DB_URL

Base = declarative_base()

async_engine = create_async_engine(url=DB_URL)
async_session = async_sessionmaker(async_engine)


class StatesUserEnum(enum.IntEnum):
    """Enum for user states."""
    START = 0
    ENTER_NAME = 1
    ENTER_LOGIN = 2
    FINISH = 3
    CREATE_TASK_START = 10
    CREATE_TASK_TITLE = 11
    CREATE_TASK_DESCRIPTION = 12
    UPDATE_TASK_START = 20
    UPDATE_TASK_TITLE = 21
    UPDATE_TASK_DESCRIPTION = 22


class User(Base):
    """User model."""
    __tablename__ = 'td_users'

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String, nullable=True)
    login: str = Column(String, unique=True, nullable=True)
    tg_id: int = Column(Integer, unique=True, nullable=False)
    status: StatesUserEnum = Column(Enum(StatesUserEnum), default=StatesUserEnum.START)
    task_id: int = Column(Integer, nullable=True)
    tasks = relationship("Task", back_populates="user")


class Task(Base):
    """Task model."""
    __tablename__ = 'td_tasks'

    id: int = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, ForeignKey('td_users.id'), nullable=False)
    title: str = Column(String(100), nullable=False)
    description: str = Column(String(300), nullable=True)
    is_complete: bool = Column(Boolean, default=False)
    is_visible: bool = Column(Boolean, default=False)
    user = relationship("User", back_populates="tasks")
