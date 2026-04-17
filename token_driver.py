from datetime import timedelta, timezone, datetime
import dotenv
import jwt
import os

dotenv.load_dotenv()


class token_driver():
    def __init__(self):
        self.ALGO = "HS256"
        self.SECRET_KEY = os.getenv("JWT_KEY")




    def create_token(self,expire_days:float,data:dict):
        data_dump = data.copy()
        data_dump["exp"] = datetime.now(tz=timezone.utc) + timedelta(days=expire_days)
        token = jwt.encode(data_dump,self.SECRET_KEY,algorithm=self.ALGO)
        return token
    

    def verify_token(self,token):
        try:
            payload = jwt.decode(token,self.SECRET_KEY,algorithms=[self.ALGO])
            return payload
        except jwt.exceptions.ExpiredSignatureError as e:
            print(e)
            return "Token Expired"
