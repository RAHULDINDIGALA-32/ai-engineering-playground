from fastapi import FastAPI, HTTPException
from test_data import products
from models import Products, ProductUpdate


app = FastAPI()

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

    return "Product NOT Found"


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




