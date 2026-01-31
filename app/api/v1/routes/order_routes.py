from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin, get_current_user
from app.schemas.order_schema import (
    OrderCreateRequest,
    OrderCreateResponse,
    OrderAddProductRequest,
    OrderRemoveProductRequest,
    OrderProductActionResponse,
    OrderDetailResponse,
    OrderedProductView,
    OrderUpdateRequest,
)

from app.services.order_service import (
    create_order_service,
    add_product_to_order_service,
    remove_product_from_order_service,
    update_order_basic_details_service,
)

from app.models.order_table import OrderTable, OrderStatus
from app.models.ordered_products import OrderedProducts

router = APIRouter()

# Get paid orders (for employees)
@router.get("/paid")
def get_paid_orders(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Endpoint for employees to fetch only paid orders.
    Returns orders where paid_at is not null.
    """
    orders = db.query(OrderTable).filter(
        OrderTable.paid_at.isnot(None)
    ).order_by(OrderTable.ordered_at.desc()).all()
    
    result = []
    for order in orders:
        # Count items in this order
        items_count = db.query(OrderedProducts).filter(OrderedProducts.order_id == order.order_id).count()
        
        result.append({
            "order_id": order.order_id,
            "user_id": order.user_id,
            "client_name": order.client_name,
            "status": order.status,
            "total_order_amount": str(order.total_order_amount),
            "ordered_at": str(order.ordered_at),
            "updated_at": str(order.updated_at),
            "invoice_generated_at": str(order.invoice_generated_at) if order.invoice_generated_at else None,
            "paid_at": str(order.paid_at) if order.paid_at else None,
            "items_count": items_count
        })
    
    return result

# Get all orders
@router.get("/all")
def get_all_orders(
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    orders = db.query(OrderTable).order_by(OrderTable.ordered_at.desc()).all()
    
    result = []
    for order in orders:
        # Count items in this order
        items_count = db.query(OrderedProducts).filter(OrderedProducts.order_id == order.order_id).count()
        
        result.append({
            "order_id": order.order_id,
            "user_id": order.user_id,
            "client_name": order.client_name,
            "status": order.status,
            "total_order_amount": str(order.total_order_amount),
            "ordered_at": str(order.ordered_at),
            "updated_at": str(order.updated_at),
            "invoice_generated_at": str(order.invoice_generated_at) if order.invoice_generated_at else None,
            "paid_at": str(order.paid_at) if order.paid_at else None,
            "items_count": items_count
        })
    
    return result

# Create Order
@router.post("/create", response_model=OrderCreateResponse)
def create_order(
    payload: OrderCreateRequest,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    order = create_order_service(db, payload)
    return OrderCreateResponse(
        order_id=order.order_id,
        status=order.status,
        message="Order created "
    )


# Add/Update product into order
@router.post("/{order_id}/add-product", response_model=OrderProductActionResponse)
def add_product(
    order_id: str,
    payload: OrderAddProductRequest,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    line, order_total = add_product_to_order_service(db, order_id, payload)

    return OrderProductActionResponse(
        order_id=order_id,
        product_id=line.product_id,
        quantity=line.quantity,
        line_total=str(line.total_price),
        order_total=str(order_total),
        message="Product added/updated "
    )


# Remove/Decrease product from order
@router.post("/{order_id}/remove-product")
def remove_product(
    order_id: str,
    payload: OrderRemoveProductRequest,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    order_total = remove_product_from_order_service(db, order_id, payload)

    return {
        "order_id": order_id,
        "product_id": payload.product_id,
        "order_total": str(order_total),
        "message": "Product removed/updated"
    }


# Get full order + products
@router.get("/{order_id}", response_model=OrderDetailResponse)
def get_order_details(
    order_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    order = db.query(OrderTable).filter(OrderTable.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # If user is not admin, only allow access to paid orders
    if current_user.role != "admin" and not order.paid_at:
        raise HTTPException(status_code=403, detail="Access denied: Order not paid")

    lines = db.query(OrderedProducts).filter(OrderedProducts.order_id == order_id).all()

    items = [
        OrderedProductView(
            product_id=l.product_id,
            quantity=l.quantity,
            unit_price=str(l.unit_price),
            rate_percentage=str(l.rate_percentage) if l.rate_percentage is not None else None,
            total_price=str(l.total_price)
        )
        for l in lines
    ]

    return OrderDetailResponse(
        order_id=order.order_id,
        user_id=order.user_id,
        client_name=order.client_name,
        status=order.status,
        total_order_amount=str(order.total_order_amount),
        ordered_at=str(order.ordered_at),
        updated_at=str(order.updated_at),
        invoice_generated_at=str(order.invoice_generated_at) if order.invoice_generated_at else None,
        paid_at=str(order.paid_at) if order.paid_at else None,
        items=items
    )

@router.patch("/{order_id}/update")
def update_order_details(
    order_id: str,
    payload: OrderUpdateRequest,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    order = update_order_basic_details_service(
        db=db,
        order_id=order_id,
        client_name=payload.client_name
    )

    return {
        "message": "Order updated ",
        "order_id": order.order_id,
        "client_name": order.client_name,
        "status": order.status,
        "updated_at": str(order.updated_at)
    }

@router.post("/{order_id}/generate-invoice")
def generate_invoice(
    order_id: str,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    from datetime import datetime
    
    order = db.query(OrderTable).filter(OrderTable.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.invoice_generated_at:
        raise HTTPException(status_code=400, detail="Invoice already generated for this order")
    
    # Update invoice_generated_at and updated_at timestamps
    order.invoice_generated_at = datetime.now()
    order.updated_at = datetime.now()
    db.commit()
    db.refresh(order)
    
    return {
        "message": "Invoice generated successfully",
        "order_id": order.order_id,
        "invoice_generated_at": str(order.invoice_generated_at),
        "updated_at": str(order.updated_at)
    }

@router.post("/{order_id}/mark-paid")
def mark_order_paid(
    order_id: str,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    from datetime import datetime
    
    order = db.query(OrderTable).filter(OrderTable.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if not order.invoice_generated_at:
        raise HTTPException(status_code=400, detail="Invoice must be generated before marking as paid")
    
    if order.paid_at:
        raise HTTPException(status_code=400, detail="Order already marked as paid")
    
    # Update paid_at, status, and updated_at timestamps
    order.paid_at = datetime.now()
    order.status = OrderStatus.IN_PROGRESS
    order.updated_at = datetime.now()
    db.commit()
    db.refresh(order)
    
    return {
        "message": "Order marked as paid successfully",
        "order_id": order.order_id,
        "paid_at": str(order.paid_at),
        "status": order.status,
        "updated_at": str(order.updated_at)
    }