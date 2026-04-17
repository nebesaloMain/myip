import asyncpg
import asyncio
import dotenv
import os

dotenv.load_dotenv()

_pool = None

async def create_pool(max_attempts: int = 10, initial_delay: float = 1.0):
    global _pool

    delay = initial_delay
    for attempt in range(1, max_attempts + 1):
        try:
            _pool = await asyncpg.create_pool(
                host=os.getenv("PG_HOST"),
                port=int(os.getenv("PG_PORT")),
                database=os.getenv("PG_DBNAME"),
                user=os.getenv("PG_USER"),
                password=os.getenv("PG_PASSWORD"),
                min_size=5,
                max_size=10,
            )
            break
        except (OSError, asyncpg.PostgresError) as exc:
            if attempt >= max_attempts:
                raise
            print(f"DB unavailable ({exc}); retrying in {delay:.1f}s [{attempt}/{max_attempts}]")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 10.0)

    print("Pool has been created")

    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

            CREATE TABLE IF NOT EXISTS users(
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                fio VARCHAR,
                username VARCHAR UNIQUE,
                email VARCHAR UNIQUE,
                job VARCHAR,
                passhash VARCHAR,
                verify_code VARCHAR,
                is_verified BOOLEAN DEFAULT FALSE,
                is_admin BOOLEAN DEFAULT FALSE
            );

            CREATE TABLE IF NOT EXISTS bids(
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                content VARCHAR,
                add_content VARCHAR,
                name VARCHAR,
                files VARCHAR[] DEFAULT '{}', 
                timestamp TIMESTAMP DEFAULT now(),
                owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                owner_username VARCHAR,
                owner_fio VARCHAR,
                owner_job VARCHAR,
                status VARCHAR DEFAULT 'new'
            );
        """)
    print("Tables ensured")

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        print("Pool has been closed")

async def get_conn():
    if _pool is None:
        raise RuntimeError("Pool is not initialized. Use create_pool first.")
    async with _pool.acquire() as conn:
        yield conn
        
