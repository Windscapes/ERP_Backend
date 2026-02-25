from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.order_table import OrderTable


def start_order_service(db: Session, order_id: str):
    order = db.query(OrderTable).filter(OrderTable.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "CREATED":
        raise HTTPException(
            status_code=400,
            detail=f"Only CREATED orders can be started. Current status={order.status}"
        )

    order.status = "IN_PROGRESS"
    order.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(order)
    return order


def complete_order_service(db: Session, order_id: str):
    order = db.query(OrderTable).filter(OrderTable.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="Order is already completed"
        )

    order.status = "COMPLETED"
    order.updated_at = datetime.utcnow()
    order.paid_at = datetime.utcnow()

    db.commit()
    db.refresh(order)
    return order
