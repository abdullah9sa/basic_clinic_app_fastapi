from pydantic import BaseModel
from datetime import datetime
from tortoise.contrib.pydantic import pydantic_model_creator
from pydantic import BaseModel
from app.models.user import *
from typing import List

# Pydantic models for input and output
UserInCreate = pydantic_model_creator(User, name="UserInCreate", exclude_readonly=True)

user_pydantic_out = pydantic_model_creator(User,name="UserOut",exclude=("password",))
# Custom Pydantic models for output
class RoleResponse(BaseModel):
    id: int
    name: str

class UserResponse(BaseModel):
    id: int
    username: str
    join_date: datetime.datetime
    role: str

class UserPasswordOutResponse(BaseModel):
    password: str

class RoleCreate(BaseModel):
    name: str

class UserCreate(BaseModel):
    username: str
    password: str
    role_id: int

class PatientCreate(BaseModel):
    name: str
    medical_info: str

class PatientOut(BaseModel):
    id: int
    name: str
    medical_info: str
    access_users: List[int]

class PatientTransferIn(BaseModel):
    receiver_id: int
    patient_id: int
    some_info: str