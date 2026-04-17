from fastapi import APIRouter, HTTPException, status
from token_driver import token_driver
from emailtool import send_email
from pydantic import BaseModel
from db import get_conn
from html import escape

import asyncio
import hashlib

_pool = None

router = APIRouter(prefix="/api/users", tags=["users"])

class User(BaseModel):
    username : str
    password : str
    fio : str
    job : str
    email : str

class UserAuth(BaseModel):
    username : str
    password : str


def hash(data):
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


@router.post("/register")
async def register(user: User):

    passhash = hash(user.password)
    
    veri_code = send_email(user.email)

    try:
        async for conn in get_conn():
            await conn.execute("INSERT INTO users (username,passhash,fio,email,job,verify_code) VALUES ($1,$2,$3,$4,$5,$6)", 
                               escape(user.username), passhash, escape(user.fio), escape(user.email), escape(user.job), veri_code)

        print("seems like we're ok")
        return {"code":200}
            
    except Exception as e:

        print("Kaput",e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@router.get("/verify/{code}")
async def verify_email(code:str):
     
    try:
        async for conn in get_conn():
            await conn.execute("UPDATE users SET is_verified = TRUE WHERE verify_code = $1;", code)
            return {"code": 200, "message": "Verified succesfully"}
    except Exception as e:
        print("Kaput", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)



@router.post("/auth")
async def authorize(user: UserAuth):

    username = user.username
    passhash = hash(user.password)
    token_thingy = token_driver()

    try:
        async for conn in get_conn():
            row = await conn.fetchval("SELECT id FROM users WHERE username = $1 AND passhash = $2;", username, passhash)
            if row:

                token = token_thingy.create_token(1,{"id":str(row),"passhash":passhash})

                return {"code":200, "token":token}
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong entering data")
            
    except HTTPException:
        raise
    except Exception as e:
        print("Kaput",e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)