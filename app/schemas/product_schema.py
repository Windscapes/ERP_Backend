from pydantic import BaseModel, Field, HttpUrl, conint, condecimal

class ProductCreateRequest(BaseModel):
    nursery_id: str = Field(..., min_length=1)
    item_name: str = Field(..., min_length=2, max_length=200)
    size: str = Field(..., min_length=1, max_length=50)

    inventory_quantity: conint(ge=0) = 0
    ordered_quantity: conint(ge=0) = 0
    low_stock_threshold: conint(ge=0) = 10

    base_price_per_unit: condecimal(gt=0, max_digits=12, decimal_places=2)
    rate_percentage: condecimal(ge=0, le=100, max_digits=5, decimal_places=2) = 0

    image_url: HttpUrl | None = None


class ProductCreateResponse(BaseModel):
    product_id: str
    message: str
