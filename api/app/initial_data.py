import asyncio

from db_models.models import User

from app.core import config, security
from app.core.db import init_db


async def main() -> None:
    print('Start initial data')
    await init_db()
    user = await User.find_one(User.username == config.settings.SUPERUSER_USERNAME)
    if user is None:
        new_superuser = User(
            username=config.settings.SUPERUSER_USERNAME,
            hashed_password=security.get_password_hash(config.settings.SUPERUSER_PASSWORD),
        )
        await new_superuser.insert()
        print('Superuser was created')
    else:
        print('Superuser already exists in database')

        print('Initial data created')


if __name__ == '__main__':
    asyncio.run(main())
