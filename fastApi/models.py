from pydantic import BaseModel

class Products(BaseModel):
    id: int
    name: str
    description: str
    price: int
    quantity: int


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: int | None = None
    quantity: int | None = None
    
