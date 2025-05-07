from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Annotated
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import uuid
import logging
from enum import Enum
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title='Complex FastAPI Example', description=
    'Demonstrating advanced FastAPI features', version='1.0.0', docs_url=
    '/api/docs', redoc_url='/api/redoc')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=
    True, allow_methods=['*'], allow_headers=['*'])
SECRET_KEY = 'your-secret-key-here'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


class UserRole(str, Enum):
    ADMIN = 'admin'
    USER = 'user'
    GUEST = 'guest'


class User(BaseModel):
    id: str = Field(default_factory=lambda : str(uuid.uuid4()))
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    disabled: bool = False
    role: UserRole = UserRole.USER
    hashed_password: str


class Item(BaseModel):
    id: str = Field(default_factory=lambda : str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None
    owner_id: str

    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v


fake_users_db = {}
fake_items_db = {}


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return User(**user_dict)
    return None


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta]=None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str=Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=status.
        HTTP_401_UNAUTHORIZED, detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User=Depends(get_current_user)
    ):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail='Inactive user')
    return current_user


async def check_admin_privileges(current_user: User=Depends(
    get_current_active_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=
            'Admin privileges required')
    return current_user


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    password: str
    role: UserRole = UserRole.USER


class UserOut(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    disabled: bool


class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


class ItemOut(ItemCreate):
    id: str
    owner_id: str


@app.post('/token', response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm=Depends()
    ):
    user = authenticate_user(fake_users_db, form_data.username, form_data.
        password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password', headers={
            'WWW-Authenticate': 'Bearer'})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={'sub': user.username},
        expires_delta=access_token_expires)
    return {'access_token': access_token, 'token_type': 'bearer'}


@app.post('/users/', response_model=UserOut)
async def create_user(user: UserCreate):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail=
            'Username already registered')
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, full_name=user
        .full_name, hashed_password=hashed_password, role=user.role)
    fake_users_db[user.username] = jsonable_encoder(db_user)
    logger.info(f'Created user: {user.username}')
    return db_user


@app.get('/users/me/', response_model=UserOut)
async def read_users_me(current_user: User=Depends(get_current_active_user)):
    return current_user


@app.get('/users/', response_model=List[UserOut])
async def read_users(current_user: User=Depends(check_admin_privileges),
    skip: int=0, limit: int=Query(default=100, le=100)):
    return list(fake_users_db.values())[skip:skip + limit]


@app.post('/items/', response_model=ItemOut)
async def create_item(item: ItemCreate, current_user: User=Depends(
    get_current_active_user)):
    db_item = Item(**item.dict(), owner_id=current_user.id)
    fake_items_db[db_item.id] = jsonable_encoder(db_item)
    logger.info(
        f'Created item: {db_item.name} for user: {current_user.username}')
    return db_item


@app.get('/items/', response_model=List[ItemOut])
async def read_items(current_user: User=Depends(get_current_active_user),
    skip: int=0, limit: int=Query(default=100, le=100), min_price: Optional
    [float]=None, max_price: Optional[float]=None):
    items = list(fake_items_db.values())
    if min_price is not None:
        items = [item for item in items if item['price'] >= min_price]
    if max_price is not None:
        items = [item for item in items if item['price'] <= max_price]
    return items[skip:skip + limit]


@app.get('/items/{item_id}', response_model=ItemOut)
async def read_item(item_id: str, current_user: User=Depends(
    get_current_active_user)):
    if item_id not in fake_items_db:
        raise HTTPException(status_code=404, detail='Item not found')
    item = fake_items_db[item_id]
    if item['owner_id'
        ] != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail=
            'Not authorized to access this item')
    return item


@app.put('/items/{item_id}', response_model=ItemOut)
async def update_item(item_id: str, item_update: ItemCreate, current_user:
    User=Depends(get_current_active_user)):
    if item_id not in fake_items_db:
        raise HTTPException(status_code=404, detail='Item not found')
    existing_item = fake_items_db[item_id]
    if existing_item['owner_id'
        ] != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail=
            'Not authorized to update this item')
    updated_item = {**existing_item, **item_update.dict()}
    fake_items_db[item_id] = updated_item
    return updated_item


@app.delete('/items/{item_id}')
async def delete_item(item_id: str, current_user: User=Depends(
    get_current_active_user)):
    if item_id not in fake_items_db:
        raise HTTPException(status_code=404, detail='Item not found')
    existing_item = fake_items_db[item_id]
    if existing_item['owner_id'
        ] != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail=
            'Not authorized to delete this item')
    del fake_items_db[item_id]
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={'message':
        exc.detail})


@app.get('/health')
async def health_check():
    return {'status': 'healthy', 'timestamp': datetime.utcnow()}
