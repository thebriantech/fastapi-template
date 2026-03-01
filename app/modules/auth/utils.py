import jwt
import bcrypt

from datetime import datetime, timedelta, timezone
from jwt.exceptions import InvalidTokenError
from app.configs import ConfigManager


def verify_password(
        plain_password, 
        hashed_password
    ):
    """Function that verify plain password

    Args:
        plain_password (string): plain password taken from user
        hashed_password (string): hased password by the system

    Returns:
        bool: Return True or False
    """    
    if isinstance(plain_password, str):
        plain_password = plain_password.encode("utf-8")
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode("utf-8")
    return bcrypt.checkpw(plain_password, hashed_password)

def get_password_hash(
        password
    ):
    if isinstance(password, str):
        password = password.encode("utf-8")
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode("utf-8")

def create_access_token(
        data: dict
    ):
    """_summary_

    Args:
        data (dict): _description_

    Returns:
        _type_: _description_
    """    
    expires_delta  = timedelta(seconds=ConfigManager.config.auth_expire_seconds)
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
                      to_encode,
                      ConfigManager.config.auth_secret_key,
                      algorithm=ConfigManager.config.auth_algorithm
                  )
    return encoded_jwt

def check_token(token):
    try:
        payload = jwt.decode(token, 
                             ConfigManager.config.auth_secret_key, 
                             algorithms=[ConfigManager.config.auth_algorithm])
        username: str = payload.get("sub")
        if username is None:
            return {
                "status": False,
                "detail": "Could not validate credential"
            }
        return {
            "status": True,
            "username": username
        }
    except InvalidTokenError:
        return {
            "status": False,
            "detail": "Could not validate credential"
        }