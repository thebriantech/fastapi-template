from typing import Union, List, Type, Optional
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    username: str
    user_group: str
    email: str
    password: str