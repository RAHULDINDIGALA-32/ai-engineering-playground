from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from test_data import products
from models import Products, ProductUpdate
from db_config import engine, get_db, SessionLocal
import db_models
import logging

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"]
)

def init_db():
    logging.info("init_db() started")

    db = SessionLocal()

    try:
        count = db.query(db_models.Product).count()

        logging.info(f"Existing products: {count}")

        if count == 0:
            logging.info("Populating database with sample data.")

            for product in products:
                db.add(
                    db_models.Product(
                        **product.model_dump()
                    )
                )

            db.commit()

            logging.info("Sample data inserted.")

        else:
            logging.info("Products already exist. Skipping initialization.")

    finally:
        db.close()
        logging.info("init_db() finished")

db_models.Base.metadata.create_all(bind=engine)

init_db()

@app.get("/")
def home():
    return {
        "message": "Welcome to the FastAPI Playground"
    }


@app.get("/products")
def get_all_products(db: Session = Depends(get_db)):

    db_products = db.query(db_models.Product).all()
    return db_products


@app.get("/produts/{id}")
def get_product_by_id(id: int, db: Session = Depends(get_db)):
    db_product = db.query(db_models.Product).filter(db_models.Product.id == id).first()
    if db_product:
        return db_product
    raise HTTPException(
        status_code=404,
        detail="Product NOT Found"
    )
    

@app.post("/products")
def create_product(product: Products, db: Session = Depends(get_db)):
    db.add(db_models.Product(**product.model_dump()))
    db.commit()
    return product

@app.put("/products/{id}")
def replace_complete_product(id: int, product: Products, db: Session = Depends(get_db)):
    db_product = db.query(db_models.Product).filter(db_models.Product.id == id).first()
    if db_product:
        update_data = product.model_dump()
        for field, value in update_data.items():
            setattr(db_product, field, value)

        db.commit()
        db.refresh(db_product)

        return db_product
    else:
        raise HTTPException(
        status_code=404,
        detail="Product Not Found"
        )


@app.patch("/products/{id}")
def update_product(id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(db_models.Product).filter(db_models.Product.id == id).first()
    if db_product:
        update_data = product.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_product, field, value)

        db.commit()
        db.refresh(db_product)

        return db_product
    else:
        raise HTTPException(
        status_code=404,
        detail="Product Not Found"
        )


@app.delete("/products/{id}")
def delete_Product(id: int, db: Session = Depends(get_db)):
    db_product = db.query(db_models.Product).filter(db_models.Product.id == id).first()
    if db_product:
        db.delete(db_product)
        db.commit()

        return db_product
    else:
        raise HTTPException(
        status_code=404,
        detail="Product Not Found"
        )



# FastAPI REST endpoints (with local-memory data)
'''

@app.get("/")
def home():
    return "Welcome to the FastAPI Playground"


@app.get("/products")
def get_all_products():
    return products


@app.get("/produts/{id}")
def get_product_by_id(id: int):
    for product in products:
        if product.id == id:
            return product

    raise HTTPException(
            status_code=404,
            detail="Product Not Found"
        )


@app.post("/products")
def create_product(product: Products):
    products.append(product)
    return product

@app.put("/products/{id}")
def replace_complete_product(id: int, product: Products):
    for index in range(len(products)):
        if products[index].id == id:
            products[index] = product
            return products[index]

    raise HTTPException(
        status_code=404,
        detail="Product Not Found"
    )


@app.patch("/products/{id}")
def update_product(id: int, product: ProductUpdate):
    for prod in products:
        if prod.id == id:

           update_data = product.model_dump(exclude_unset=True)

           for field, value in update_data.items():
            setattr(prod, field, value)

            return prod

    raise HTTPException(
        status_code=404,
        detail="Product Not Found"
    )


@app.delete("/products/{id}")
def delete_Product(id: int):
    for index, prod in enumerate(products):
        if prod.id == id:
            deleted_product = products.pop(index)
            return deleted_product

    raise HTTPException(
        status_code=404,
        detail="Product Not Found"
    )


'''

