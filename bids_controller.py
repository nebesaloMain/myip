from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Form, File
from typing import List
from token_driver import token_driver
from pydantic import BaseModel
from db import get_conn
from html import escape
import uuid
import os

router = APIRouter(prefix="/api/bids", tags=["bids"])

class Bid(BaseModel):
    content : str
    add_content : str = None
    files : list[UploadFile] = None
    name : str

class StatusUpdate(BaseModel):
    id: str
    status: str

security = HTTPBearer()

@router.post("/createnew")
async def create_bid(
    name: str = Form(...), 
    content: str = Form(...), 
    add_content: str = Form(...),


    files: List[UploadFile] = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)):

    token_thingy = token_driver()
    auth_header = credentials.credentials
    payload = token_thingy.verify_token(auth_header)

    if not payload:
        print("Wrongie Token, ur Unauthorized")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrrect token")


    id = payload["id"]
    passhash = payload["passhash"]

    filenames = []

    if files:
        for file in files:
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            
            file_path = os.path.join("uploads", unique_filename)

            try:
                decoded_name = file.filename.encode('latin-1').decode('utf-8')
            except UnicodeDecodeError:
                decoded_name = file.filename 
            

            try:
                with open(file_path, "wb") as buffer:
                    fcontent = await file.read()
                    buffer.write(fcontent)
                filenames.append(decoded_name)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Ошибка при сохранении файла: {e}")
            finally:
                await file.close()

    try:
        async for conn in get_conn():
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1 AND passhash = $2 AND is_verified = TRUE;", id, passhash)
            if row:
                await conn.execute("INSERT INTO bids (name,add_content,content,owner_id,owner_username,owner_fio,owner_job,files) VALUES ($1,$2,$3,$4,$5,$6,$7,$8);",
                                    escape(name), escape(add_content), escape(content), row["id"], row["username"], row["fio"], row["job"],filenames)
            else:
                print("Wrongie Token, ur Unauthorized")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect token or email not veryfied")



        print("seems like we're ok")
        return {"code":200}
            
    except Exception as e:

        print("Kaput",e)
        if str(e) != "401: Incorrect token or email not veryfied":
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect token or email not veryfied")


@router.get("/getone")
async def get_bid(id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_thingy = token_driver()
    auth_header = credentials.credentials
    payload = token_thingy.verify_token(auth_header)

    if not payload:
        print("Wrongie Token, ur Unauthorized")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrrect token")
    
    if payload == "Token Expired":
        print("Token Expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

    try:
        async for conn in get_conn():
                row = await conn.fetchval("SELECT is_admin FROM users WHERE id = $1 AND passhash = $2;", payload["id"], payload["passhash"])
                if row:
                    pass
                    
                else:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not valid")
            
    except Exception as e:
        print("Kaput", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)





    if not row:
        try:
            async for conn in get_conn():

                row = await conn.fetchrow("SELECT * FROM bids WHERE id = $1;", id)
                if row["owner_id"] != payload["id"]:
                    print("Not ur bid, ur Forbidden")
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not an owner or admin")
                    
        except Exception as e:
            print("Kaput",e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    try:
        async for conn in get_conn():
            row = await conn.fetchrow("SELECT * FROM bids WHERE id = $1;", id)
            if row:
                return {"code":200,"bid":row}
            else:
                print("Bid not found, ur Not Found")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No bid with such id")
    except Exception as e:
        print("Kaput",e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/getall")
async def get_all_bids(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_thingy = token_driver()
    auth_header = credentials.credentials
    payload = token_thingy.verify_token(auth_header)

    if not payload:
        print("Wrongie Token, ur Unauthorized")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrrect token")
    
    if payload == "Token Expired":
        print("Token Expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        
    try:
        async for conn in get_conn():
                row = await conn.fetchval("SELECT is_admin FROM users WHERE id = $1 AND passhash = $2;", payload["id"], payload["passhash"])
                if row:


                    rows = await conn.fetch("SELECT id, name, status, owner_username, timestamp FROM bids;")
                    return {"code": 200, "bids": rows}
                    
                else:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not an admin")
            
    except Exception as e:
        print("Kaput", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.patch("/changestat")
async def change_status(update: StatusUpdate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_thingy = token_driver()
    auth_header = credentials.credentials
    payload = token_thingy.verify_token(auth_header)

    if not payload:
        print("Wrongie Token, ur Unauthorized")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrrect token")
    
    try:
        async for conn in get_conn():
                row = await conn.fetchval("SELECT is_admin FROM users WHERE id = $1 AND passhash = $2;", payload["id"], payload["passhash"])
                if row:
                    pass
                    
                else:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not an admin")
            
    except Exception as e:
        print("Kaput", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
    try:
        async for conn in get_conn():
            await conn.execute("UPDATE bids SET status = $1 WHERE id = $2;", update.status, update.id)
            return {"code": 200, "message": "Status updated"}
    except Exception as e:
        print("Kaput", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.delete("/deleteone")
async def delete_bid(id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_thingy = token_driver()
    auth_header = credentials.credentials
    payload = token_thingy.verify_token(auth_header)

    if not payload:
        print("Wrongie Token, ur Unauthorized")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect token")
    

    if payload == "Token Expired":
        print("Token Expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

    try:
        async for conn in get_conn():
                row = await conn.fetchval("SELECT is_admin FROM users WHERE id = $1 AND passhash = $2;", payload["id"], payload["passhash"])
                if row:
                    pass
                    
                else:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not an admin")
    except Exception as e:
        print("Kaput", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)



    try:
        async for conn in get_conn():
            row = await conn.fetchrow("SELECT files FROM bids WHERE id = $1;", id)
            if row and row["files"]:
                for filename in row["files"]:
                    file_path = os.path.join("uploads", filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
            await conn.execute("DELETE FROM bids WHERE id = $1;", id)
            return {"code": 200, "message": "Bid deleted"}
    except Exception as e:
        print("Kaput", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@router.get("/file")
async def get_file(id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_thingy = token_driver()
    auth_header = credentials.credentials
    payload = token_thingy.verify_token(auth_header)

    if not payload:
        print("Wrongie Token, ur Unauthorized")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrrect token")
    
    if payload == "Token Expired":
        print("Token Expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

    try:
        async for conn in get_conn():
                row = await conn.fetchval("SELECT is_admin FROM users WHERE id = $1 AND passhash = $2;", payload["id"], payload["passhash"])
                if row:
                    pass
                    
                else:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not valid")
            
    except Exception as e:
        print("Kaput", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)





    if not row:
        try:
            async for conn in get_conn():

                row = await conn.fetchrow("SELECT * FROM bids WHERE id = $1;", id)
                if row["owner_id"] != payload["id"]:
                    print("Not ur bid, ur Forbidden")
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not an owner or admin")
                    
        except Exception as e:
            print("Kaput",e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    try:
        async for conn in get_conn():
            row = await conn.fetchrow("SELECT * FROM bids WHERE id = $1;", id)
            if row:
                return {"code":200,"bid":row}
            else:
                print("Bid not found, ur Not Found")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No bid with such id")
    except Exception as e:
        print("Kaput",e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
