from pydantic import BaseModel, Field, conint, condecimal
from typing import Optional, List

class OrderCreateRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    client_name: str = Field(..., min_length=2, max_length=200)


class OrderCreateResponse(BaseModel):
    order_id: str
    status: str
    message: str


class OrderAddProductRequest(BaseModel):
    product_id: str = Field(..., min_length=1)
    quantity: conint(gt=0)
    unit_price: condecimal(gt=0, max_digits=12, decimal_places=2)
    rate_percentage: Optional[condecimal(ge=0, le=100, max_digits=5, decimal_places=2)] = None


class OrderProductActionResponse(BaseModel):
    order_id: str
    product_id: str
    quantity: int
    line_total: str
    order_total: str
    message: str


class OrderRemoveProductRequest(BaseModel):
    product_id: str = Field(..., min_length=1)
    quantity: Optional[conint(gt=0)] = None


class OrderedProductView(BaseModel):
    product_id: str
    quantity: int
    unit_price: str
    rate_percentage: str | None
    total_price: str


class OrderDetailResponse(BaseModel):
    order_id: str
    user_id: str
    client_name: str
    status: str
    total_order_amount: str
    ordered_at: str
    updated_at: str
    invoice_generated_at: Optional[str] = None
    paid_at: Optional[str] = None
    items: List[OrderedProductView]


class OrderUpdateRequest(BaseModel):
    client_name: str
