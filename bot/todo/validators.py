from database.repository import Repository


def is_valid_name(name: str) -> None:
    return not name.startswith("/")


async def is_valid_login(login) -> None:
    return is_valid_name(login) and not (await Repository.user_exists_by_login(login))