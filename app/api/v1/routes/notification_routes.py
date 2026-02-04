from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.deps import get_db, require_admin
from app.models.product import Product
from app.models.user import UserTable
from pydantic import BaseModel

router = APIRouter()

class LowStockNotification(BaseModel):
    product_id: str
    item_name: str
    size: str
    current_stock: int
    threshold: int
    nursery_id: str

    class Config:
        from_attributes = True

@router.get("/low-stock", response_model=List[LowStockNotification])
def get_low_stock_items(
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(require_admin)
):
    """
    Get all products with inventory below their low stock threshold (Admin only)
    """
    low_stock_products = db.query(Product).filter(
        Product.inventory_quantity <= Product.low_stock_threshold
    ).all()
    
    notifications = [
        LowStockNotification(
            product_id=product.product_id,
            item_name=product.item_name,
            size=product.size,
            current_stock=product.inventory_quantity,
            threshold=product.low_stock_threshold,
            nursery_id=product.nursery_id
        )
        for product in low_stock_products
    ]
    
    return notifications
