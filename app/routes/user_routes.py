from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.models.user import *
import datetime
import bcrypt
import jwt
from fastapi import HTTPException
from app.serializers.serializers import *
from app.models.user import User
import jwt

router = APIRouter()

SECRET_KEY = "12345678"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def authenticate_user(username: str, password: str):
    user = await User.get_or_none(username=username)  # Use get_or_none to get a single user
    if user:
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            print(f"Password hash of user {username}: {user.password}")
            return user

def create_access_token(data: dict, expires_delta: datetime.timedelta):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "Bearer"}

@router.get("/{user_id}", response_model=UserResponse, summary="Get User by ID", description="Retrieve user details by providing their ID.")
async def get_user(user_id: int):
    """
    Get User by ID
    Retrieve user details by providing their ID.
    
    :param user_id: ID of the user to retrieve.
    :return: User details.
    """
    user = await User.get_or_none(id=user_id)
    
    if user is None:
        error_msg = f"User with ID {user_id} not found"
        error_detail = {"error": error_msg}
        raise HTTPException(status_code=404, detail=error_detail)
    
    role = await user.role.first()  # Get the first Role instance from the queryset

    user_out_response = UserResponse(
        id=user.id,
        username=user.username,
        join_date=user.join_date,
        role=role.name
    )
    return user_out_response


@router.post("/register", response_model=UserResponse, summary="Register User", description="Register a new user.")
async def register_user(user_data: UserCreate):
    """
    Register User
    Register a new user.
    
    :param user_data: User data including username, email, password, and role_id.
    :return: Registered user details.
    """
    # Hash the password using bcrypt
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())

    # Create a new user using the data from the request
    new_user = await User.create(
        username=user_data.username,
        password=hashed_password.decode('utf-8'),  # Store the hashed password in the database
        role_id=user_data.role_id
    )
    role = await new_user.role.first()  # Get the first Role instance from the queryset

    user_response = UserResponse(
        id=new_user.id,
        username=new_user.username,
        join_date=new_user.join_date,
        role=role.name
    )
    return user_response


