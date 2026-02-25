from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

from app.core.deps import get_db, get_current_user
from app.models.user import UserTable
from app.models.employee_scan_log import EmployeeScanLog
from app.models.product import Product
from app.models.order_table import OrderTable
from app.models.ordered_products import OrderedProducts

router = APIRouter()


class ScanRequest(BaseModel):
    order_id: str
    product_id: str
    quantity_scanned: int = 1


@router.post("/scan")
def record_scan(
    payload: ScanRequest,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    Record a barcode scan for an employee working on an order.
    Reduces the product's inventory_quantity by the scanned amount.
    """
    if payload.quantity_scanned <= 0:
        raise HTTPException(status_code=400, detail="quantity_scanned must be positive")

    # Validate order exists and is in a scannable state
    order = db.query(OrderTable).filter(OrderTable.order_id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Order is already completed")

    # Validate product exists in the order
    order_item = db.query(OrderedProducts).filter(
        OrderedProducts.order_id == payload.order_id,
        OrderedProducts.product_id == payload.product_id,
    ).first()
    if not order_item:
        raise HTTPException(
            status_code=404,
            detail="Product not found in this order"
        )

    # Fetch product
    product = db.query(Product).filter(Product.product_id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Deduct inventory (floor at 0)
    deduct = min(payload.quantity_scanned, product.inventory_quantity)
    product.inventory_quantity = max(0, product.inventory_quantity - payload.quantity_scanned)

    # Create scan log
    scan_log = EmployeeScanLog(
        scan_id=f"scn_{uuid.uuid4().hex[:12]}",
        employee_id=current_user.user_id,
        order_id=payload.order_id,
        product_id=payload.product_id,
        scanned_quantity=payload.quantity_scanned,
    )
    db.add(scan_log)
    db.commit()
    db.refresh(product)

    return {
        "scan_id": scan_log.scan_id,
        "product_id": product.product_id,
        "quantity_scanned": payload.quantity_scanned,
        "new_inventory_quantity": product.inventory_quantity,
        "message": "Scan recorded successfully",
    }


@router.get("/scans")
def get_scan_logs_for_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user),
):
    """
    Return all scan logs for a given order, aggregated per product.
    Used to restore scanned_quantity when loading the order page.
    """
    logs = (
        db.query(EmployeeScanLog)
        .filter(EmployeeScanLog.order_id == order_id)
        .all()
    )

    # Aggregate per product
    totals: dict[str, int] = {}
    for log in logs:
        totals[log.product_id] = totals.get(log.product_id, 0) + log.scanned_quantity

    return {"order_id": order_id, "scanned_quantities": totals}
