from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError

from database.models import async_session, User, Task


class Repository:
    """
    Repository class implementing data access methods.
    """
    async_session = async_session

    @staticmethod
    async def create_user(tg_id: str) -> User:
        """
        Create a new user with the specified Telegram ID.
        """
        async with Repository.async_session() as session:
            new_user = User(tg_id=tg_id)
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user

    @staticmethod
    async def get_user(tg_id: str = None) -> User:
        """
        Get a user based on the Telegram ID.
        """
        async with Repository.async_session() as session:
            statement = select(User).where(User.tg_id == tg_id)
            result = await session.execute(statement)
            return result.scalar_one_or_none()

    @staticmethod
    async def user_exists_by_login(login: str) -> bool:
        """
        Check if a user with the given login exists.
        """
        async with Repository.async_session() as session:
            stmt = select(User).where(User.login == login)
            result = await session.execute(stmt)
            user = result.scalar()
            return user is not None

    @staticmethod
    async def get_task(user, task_id=None):
        """
        Get a task for the specified user and task ID.
        """
        result = await Repository.get_tasks(user, params={"id": task_id if task_id else user.task_id})
        return result[0][0] if result else []

    @staticmethod
    async def get_tasks(user, params: dict) -> User:
        """
        Get tasks for the specified user based on parameters.
        """
        async with Repository.async_session() as session:
            statement = select(Task).where(
                Task.user_id == user.id,
                *[getattr(Task, param) == value for param, value in params.items()]
            )
            result = await session.execute(statement)
            return result.fetchall()

    @staticmethod
    async def find_models(db_model, params):
        """
        Find models in the database based on the specified parameters.
        """
        async with Repository.async_session() as session:
            db_models = await session.query(db_model).filter_by(**params).all()
            return db_models

    @staticmethod
    async def delete_not_visible_task(user):
        """
        Delete tasks that are not visible for the specified user.
        """
        async with Repository.async_session() as session:
            stmt = delete(Task).where(Task.is_visible == False, Task.user_id == user.id)
            await session.execute(stmt)
            await session.commit()

    @staticmethod
    async def save(*models):
        """
        Save models in the database.
        """
        async with Repository.async_session() as session:
            for model in models:
                session.add(model)
            try:
                await session.flush()
                await session.commit()
                for model in models:
                    await session.refresh(model)
                return True, models
            except IntegrityError:
                return False, models
            except Exception:
                return False, models

    @staticmethod
    async def delete_task(user, task_id) -> User:
        """
        Delete a task for the specified user and task ID.
        """
        async with Repository.async_session() as session:
            statement = delete(Task).where(
                Task.user_id == user.id, Task.id == task_id
            )
            result = await session.execute(statement)
            await session.commit()
            return result
