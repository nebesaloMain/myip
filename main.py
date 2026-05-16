from userslogic_controller import router as users_router
from fastapi.middleware.cors import CORSMiddleware
from bids_controller import router as bids_router
from contextlib import asynccontextmanager
from db import create_pool, close_pool
from fastapi import FastAPI

import uvicorn



@asynccontextmanager
async def lifespan(app: FastAPI):

    await create_pool()
    yield

    await close_pool()

_pool = None

app = FastAPI(lifespan=lifespan)

app.include_router(users_router)
app.include_router(bids_router)

app.add_middleware(CORSMiddleware, 
                    allow_origins=[
                        "https://nebesalo.ru",
                        "https://nebesalo.ru:443",
                        "https://nebesalo.ru:80",
                        "http://localhost",
                        "http://localhost:5500",
                        "http://localhost:5500",
                        "127.0.0.1:5500"
                    ], 
                    allow_credentials=True,
                    allow_methods=["*"], 
                    allow_headers=["*"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
