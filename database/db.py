import orjson


from config import Settings
import aiofiles
from typing import List, Tuple, Optional, Union

import asyncpg


settings = Settings()
DATABASE_URL = settings.get_db_url()


_pool: asyncpg.Pool | None = None


class Sqlbase:

    def __init__(self, pool=None):
        self.pool = pool or _pool

    @classmethod
    async def init_pool(cls, ):
        """
        Создаёт глобальный пул, который будет использоваться всеми наследниками.
        Возможно, стоит переделать
        """

        global _pool

        async def switch_schema(connection: asyncpg.Connection):
            await connection.execute(f'''SET search_path TO "{settings.current_schema}"''')

        if _pool is None:
            _pool = await asyncpg.create_pool(
                dsn=DATABASE_URL,
                setup=switch_schema,
                min_size=1,
                max_size=100,
            )

        return _pool

    @classmethod
    async def close_pool(cls):
        """
        Закрытие пула для всех наследников
        :return:
        """
        global _pool
        if _pool:
            await _pool.close()
            _pool = None

    async def execute_query(self, query, params=None):
        """
        Создание транзакции с запросами и их параметрами
        :param query:
        :param params:
        :return:
        """
        pool = self.pool or _pool
        if not pool:
            raise ValueError("Пул соединений не создан. Убедитесь, что вызвали Sqlbase.init_pool().")

        try:
            async with pool.acquire() as connection:
                await connection.set_type_codec('jsonb',
                                                encoder=orjson.dumps,
                                                decoder=orjson.loads,
                                                schema="pg_catalog",)
                async with connection.transaction():

                    if params:
                        return await connection.fetchval(query, *params)
                    return await connection.fetchval(query)
        except asyncpg.PostgresError as e:
            print(f"Ошибка выполнения запроса: {e}")
            raise

    async def execute_transaction(
            self,
            queries: List[Tuple[str, Optional[tuple]]]
    ) -> List[Union[list, None]]:
        """
        Выполняет несколько SQL-запросов в рамках одной транзакции.
        :param queries: список кортежей (sql, params)
        :return: список результатов выполнения запросов
        """
        pool = self.pool or _pool

        if not pool:
            raise ValueError("Пул соединений не создан. Убедитесь, что вызвали connect().")

        results = []
        try:
            async with pool.acquire() as connection:
                async with connection.transaction():
                    for query, params in queries:
                        if params:
                            result = await connection.fetch(query, *params)
                        else:
                            result = await connection.fetch(query)
                        results.append(result)
            return results

        except asyncpg.PostgresError as e:
            print(f"Ошибка выполнения транзакции: {e}")
            raise

    async def execute_file(self, filepath: str):
        """
        Совершение sql-кода из какого-либо файла.

        P.s: Хоть и используется Aiofiles, но т.к его работа всё ещё блокирующая, рекомендуется использовать другие методы
        :param filepath: - путь до файла
        :return:
        """
        pool = self.pool or _pool
        try:
            if not pool:
                raise ValueError("Пул соединений не создан. Убедитесь, что вызвали Sqlbase.init_pool().")

            async with aiofiles.open(file=filepath, mode="r") as file:
                sql_reader = await file.read()
            if sql_reader:
                await self.execute_query(f"{sql_reader}")
        except asyncpg.PostgresError as e:
            print(f"Ошибка выполнения транзакции: {e}")
            raise

