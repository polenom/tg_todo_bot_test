from typing import Optional, List, Tuple

from pyrogram.types import KeyboardButton
from sqlalchemy.exc import IntegrityError

from database.models import User, Task, StatesUserEnum
from database.repository import Repository
from todo.buttons import BUTTONS_AFTER_REGISTRATION
from todo.validators import is_valid_name, is_valid_login


class BaseAction:
    """Base class for user actions."""

    async_session = Repository.async_session

    def __init__(self, user: User) -> None:
        self._user: User = user
        self._text: Optional[str] = None
        self._required_save: bool = False
        self._message: str = ""
        self._buttons: Optional[List[List[KeyboardButton]]] = None

    async def start_action(self) -> Tuple[str, Optional[List[List[KeyboardButton]]]]:
        """Method to be called when starting the user action."""
        raise NotImplementedError("Subclasses must implement start_action.")

    async def continue_action(self, text: str) -> Tuple[str, Optional[List[List[KeyboardButton]]]]:
        """Method to be called when continuing the user action."""
        raise NotImplementedError("Subclasses must implement continue_action.")

    async def _fsm_strategy(self) -> Tuple[str, Optional[List[List[KeyboardButton]]]]:
        """Finite State Machine (FSM) strategy to handle different user states."""
        raise NotImplementedError("Subclasses must implement _fsm_strategy.")

    async def _save_models(self) -> bool:
        """Save user and related models to the database."""
        raise NotImplementedError("Subclasses must implement _save_models.")


class RegistrationUser(BaseAction):

    async def start_action(self) -> Tuple[str, Optional[List[List[KeyboardButton]]]]:
        if self._user.status < StatesUserEnum.FINISH:
            self._user.status = StatesUserEnum.START
        return await self._fsm_strategy()

    async def continue_action(self, text) -> Tuple[str, Optional[List[List[KeyboardButton]]]]:
        self._text = text
        return await self._fsm_strategy()

    async def _fsm_strategy(self) -> Tuple[str, Optional[List[List[KeyboardButton]]]]:
        if self._user.status == StatesUserEnum.START:
            self._user.status = StatesUserEnum.ENTER_NAME
            self._message = "Введите имя пользователся"
            self._required_save = True
        elif self._user.status == StatesUserEnum.ENTER_NAME:
            if is_valid_name(self._text):
                self._user.name = self._text
                self._user.status = StatesUserEnum.ENTER_LOGIN
                self._message = "Введите имя логин"
                self._required_save = True
            else:
                self._message = "Введенное имя не подходит"
        elif self._user.status == StatesUserEnum.ENTER_LOGIN:
            if await is_valid_login(self._text):
                self._user.login = self._text
                self._user.status = StatesUserEnum.FINISH
                self._message = "Поздравляю вы зарегистрировались"
                self._buttons = BUTTONS_AFTER_REGISTRATION
                self._required_save = True
            else:
                self._message = "Введенный логин не подходит"
        else:
            self._message = "Вы уже зарегистрированы"
        if self._required_save and not await self._save_models():
            raise Exception("Ошибка при сохранение")
        return self._message, self._buttons

    async def _save_models(self):
        async with self.async_session() as session:
            session.add(self._user)
            try:
                await session.flush()
                await session.commit()
                await session.refresh(self._user)
                return True
            except IntegrityError:
                return False
            except Exception:
                return False


class CreateTask(BaseAction):
    async def start_action(self):
        await Repository.delete_not_visible_task(self._user)
        self._user.status = StatesUserEnum.CREATE_TASK_START
        return await self._fsm_strategy()

    async def continue_action(self, text):
        self._text = text
        return await self._fsm_strategy()

    async def _fsm_strategy(self):
        if self._user.status == StatesUserEnum.CREATE_TASK_START:
            self._user.status = StatesUserEnum.CREATE_TASK_TITLE
            self._message = "Введите название задачи"
            self._required_save = True
        elif self._user.status == StatesUserEnum.CREATE_TASK_TITLE:
            self._task = Task(
                user_id=self._user.id,
                title=self._text
            )
            self._message = "Введите описание задачи"
            self._user.status = StatesUserEnum.CREATE_TASK_DESCRIPTION
            self._required_save = True
        elif self._user.status == StatesUserEnum.CREATE_TASK_DESCRIPTION:
            self._task: Task = await Repository.get_task(self._user)
            self._task.description = self._text
            self._task.is_visible = True
            self._user.status = StatesUserEnum.FINISH
            self._message = "Задача была создана"
            self._required_save = True
        if self._required_save and not await self._save_models():
            raise Exception("Ошибка при сохранение")
        return self._message, self._buttons

    async def _save_models(self):
        async with self.async_session() as session:
            try:
                if hasattr(self, '_task'):
                    session.add(self._task)
                    await session.commit()
                    await session.refresh(self._task)
                    self._user.task_id = self._task.id
                session.add(self._user)
                await session.commit()
                await session.refresh(self._user)
                return True
            except IntegrityError:
                return False
            except Exception:
                return False


class UpdateTask(BaseAction):

    async def start_action(self):
        self._user.status = StatesUserEnum.UPDATE_TASK_START
        return await self._fsm_strategy()

    async def continue_action(self, text):
        self._text = text
        return await self._fsm_strategy()

    async def _fsm_strategy(self):
        self._required_save = True
        if self._user.status == StatesUserEnum.UPDATE_TASK_START:
            self._user.status = StatesUserEnum.UPDATE_TASK_TITLE
            self._message = "Введите новое название задачи"
            self._required_save = True
        elif self._user.status == StatesUserEnum.UPDATE_TASK_TITLE:
            self._task = await Repository.get_task(self._user)
            self._task.title = self._text
            self._message = "Введите новое описание задачи"
            self._user.status = StatesUserEnum.UPDATE_TASK_DESCRIPTION
            self._required_save = True
        elif self._user.status == StatesUserEnum.UPDATE_TASK_DESCRIPTION:
            self._task: Task = await Repository.get_task(self._user)
            self._task.description = self._text
            self._user.status = StatesUserEnum.FINISH
            self._message = "Задача была обновлена"
            self._required_save = True
        if self._required_save and not await self._save_models():
            raise Exception("Ошибка при сохранение")
        return self._message, self._buttons

    async def _save_models(self):
        async with self.async_session() as session:
            try:
                if hasattr(self, '_task'):
                    session.add(self._task)
                    await session.commit()
                    await session.refresh(self._task)
                session.add(self._user)
                await session.commit()
                await session.refresh(self._user)
                return True
            except IntegrityError:
                return False
            except Exception:
                return False
