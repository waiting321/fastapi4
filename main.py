from typing import Optional
from fastapi import *
from pydantic.utils import ClassAttribute
from sqlalchemy.orm import Session
from pydantic import BaseModel
from starlette.routing import PARAM_REGEX
from starlette.status import *
from database import SessionLocal, engine
from models import *
import oauth2
from fastapi.security import OAuth2PasswordRequestForm
app = FastAPI() # create instance

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AccountLogin(BaseModel):
    email: str
    password: str


class ProductsChange(BaseModel):
    id:int
    name:Optional[str]=None
    price:Optional[int]=None
    image:Optional[str]=None
    quantityinstock:Optional[int]=None
    category:Optional[str]=None



class AccountRegister(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phoneNumber: Optional[str] = None
    address: Optional[str] = None
    password: Optional[str] = None
    confirmPassword: Optional[str] = None

class AccountInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phoneNumber: Optional[str] = None
    address: Optional[str] = None


class Token(BaseModel):
    access_token:str
    

class TokenData(BaseModel):
    id:int
    role:Optional[str]=None

"""

Login

"""
@app.post("/auth")
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

    if user.password != user_credentials.password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

    # create a token
    # return token

    access_token = oauth2.create_access_token(data = {"user_id": user.userID, "role": user.role})

    return {"access_token": access_token, "token_type": "bearer"}

        

"""

Log out

"""

@app.get("/logout/{id}")
async def log_out(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.userID == id).first()
    user.isActive = False
    db.commit()

    return db.query(User).filter(User.userID == id).first()

"""

Register

"""

@app.post("/auth/register")
async def register(acc: AccountRegister, db: Session = Depends(get_db)):
    acc_dict = acc.dict()

    # No duplicate account/email in database
    if (db.query(User).filter(User.email == acc_dict['email']).first() == None):
        if(acc_dict['password'] == acc_dict['confirmPassword']):
            db_user = User(email = acc_dict['email'],
                        password = acc_dict['password'],
                        name = acc_dict['name'],
                        address = acc_dict['address'],
                        phoneNumber = acc_dict['phoneNumber'],
                        role = "Member",
                        isActive = True)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        else: raise HTTPException(status_code = HTTP_400_BAD_REQUEST, detail = "Confirm Password incorrect")
    else: raise HTTPException(status_code = HTTP_400_BAD_REQUEST, detail = "Email existed")

    return db.query(User).all()

"""

Change Pass

"""

@app.put("/account/change-password/{id}")
async def change_password(id: int, acc: AccountRegister, db: Session = Depends(get_db)):
    acc_dict = acc.dict()
    if (acc_dict['password'] == acc_dict['confirmPassword']):
        post_query = db.query(User).filter(User.userID == id)
        post_query.update({"password": acc_dict["password"]}, synchronize_session=False)
        db.commit()
    else: raise HTTPException(status_code = HTTP_400_BAD_REQUEST, detail = "Confirm Password incorrect")

    return post_query.first()

"""

Change Info

"""

@app.put("/account/change-information/{id}")
async def change_info(id: int, acc: AccountInfo, db: Session = Depends(get_db)):
    acc_dict = acc.dict()
    post_query = db.query(User).filter(User.userID == id)
    post_query.update(acc_dict, synchronize_session=False)
    db.commit()
    return post_query.first()


"""

View Account

"""
@app.get("/account/{id}")
async def change_info(id: int, db: Session = Depends(get_db)):
    return db.query(User).get(id)

'Get Landing Page'

@app.get("/get-landing-page")
async def view_product( db: Session = Depends(get_db),user_id:int =Depends(oauth2.get_current_user)):
    print (user_id)
    return db.query(Products).all()


'Get Product Detail'
@app.get("/product/get-detail/{id}")
async def get_product_details(id: int, db: Session = Depends(get_db)):

    return db.query(Products).get(id)


'Get Category'

@app.get("/product/get-category/{type}")
async def get_category(type:str,db: Session = Depends(get_db)):
    return db.query(Products).filter(Products.category==type).all()

'Search Product'

@app.get("/search/{info}")
async def search_product(info:str,db: Session = Depends(get_db)):
    queue=db.query(Products).filter(Products.name.contains(info)).all()
    return queue

'Delete Product'

@app.delete("/delete-product/{id}")
async def delete_product(id:int,db: Session = Depends(get_db)):
    product_delete=db.query(Products).filter(Products.productID==id).first()

    if product_delete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Khong co product")
    db.delete(product_delete)
    db.commit()
    return db.query(Products).all()

'Change Product'

@app.post("/change-product")
async def changer_product(product:ProductsChange,db:Session=Depends(get_db)):
    product_dict= product.dict()
    product_change=db.query(Products).filter(Products.productID==product.id).first()
    if product_change is not None:
        product_change.productID=product.id
        product_change.name=product.name
        product_change.price=product.price
        product_change.quantityInStock=product.quantityinstock
        product_change.image1=product.image
        product_change.category=product.category
        db.commit()
    else:
        new_product=Products(
            productID = product.id,
            name = product.name,
            image1 = product.image,
            quantityInStock=product.quantityinstock,
            price = product.price,
            category=product.category
        )
        db.add(new_product)
        db.commit()
    
    return db.query(Products).all()
