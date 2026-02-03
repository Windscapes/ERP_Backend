from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.core.deps import get_db, require_admin
from app.models.order_table import OrderTable, OrderStatus
from app.models.ordered_products import OrderedProducts
from app.models.product import Product
from app.models.user import UserTable

router = APIRouter()

@router.get("/overview")
def get_analytics_overview(
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Get overall analytics overview including revenue, orders, products, and employees
    """
    # Total revenue from all orders
    total_revenue = db.query(func.sum(OrderTable.total_order_amount)).scalar() or 0
    
    # Total number of orders
    total_orders = db.query(OrderTable).count()
    
    # Total number of products
    total_products = db.query(Product).count()
    
    # Count employees (users with role='employee')
    active_employees = db.query(UserTable).filter(UserTable.role == 'employee').count()
    
    # Count orders by status
    orders_by_status = {}
    for status in OrderStatus:
        count = db.query(OrderTable).filter(OrderTable.status == status).count()
        orders_by_status[status.value] = count
    
    # Revenue last 30 days vs previous 30 days for growth calculation
    thirty_days_ago = datetime.now() - timedelta(days=30)
    sixty_days_ago = datetime.now() - timedelta(days=60)
    
    revenue_last_30 = db.query(func.sum(OrderTable.total_order_amount))\
        .filter(OrderTable.ordered_at >= thirty_days_ago)\
        .scalar() or 0
    
    revenue_previous_30 = db.query(func.sum(OrderTable.total_order_amount))\
        .filter(
            OrderTable.ordered_at >= sixty_days_ago,
            OrderTable.ordered_at < thirty_days_ago
        )\
        .scalar() or 0
    
    revenue_growth = 0
    if revenue_previous_30 > 0:
        revenue_growth = ((float(revenue_last_30) - float(revenue_previous_30)) / float(revenue_previous_30)) * 100
    
    # Orders growth
    orders_last_30 = db.query(OrderTable).filter(OrderTable.ordered_at >= thirty_days_ago).count()
    orders_previous_30 = db.query(OrderTable).filter(
        OrderTable.ordered_at >= sixty_days_ago,
        OrderTable.ordered_at < thirty_days_ago
    ).count()
    
    orders_growth = 0
    if orders_previous_30 > 0:
        orders_growth = ((orders_last_30 - orders_previous_30) / orders_previous_30) * 100
    
    return {
        "total_revenue": str(total_revenue),
        "total_orders": total_orders,
        "total_products": total_products,
        "active_employees": active_employees,
        "orders_by_status": orders_by_status,
        "revenue_growth": round(revenue_growth, 2),
        "orders_growth": round(orders_growth, 2)
    }

@router.get("/designers")
def get_designer_analytics(
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Get performance metrics for designers/admins
    """
    # Get all admin users
    admins = db.query(UserTable).filter(UserTable.role == 'admin').all()
    
    designer_stats = []
    for admin_user in admins:
        # Get orders created by this admin
        orders = db.query(OrderTable).filter(OrderTable.user_id == admin_user.user_id).all()
        
        order_count = len(orders)
        total_revenue = sum(float(order.total_order_amount) for order in orders)
        avg_order_value = total_revenue / order_count if order_count > 0 else 0
        
        designer_stats.append({
            "user_id": admin_user.user_id,
            "username": admin_user.user_username,
            "orders": order_count,
            "revenue": str(total_revenue),
            "avg_order_value": str(round(avg_order_value, 2))
        })
    
    # Sort by revenue descending
    designer_stats.sort(key=lambda x: float(x["revenue"]), reverse=True)
    
    return designer_stats

@router.get("/products/top")
def get_top_products(
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
    limit: int = 10
):
    """
    Get top selling products by quantity sold and revenue
    """
    # Query products with their sales data
    product_sales = db.query(
        Product.product_id,
        Product.item_name,
        func.sum(OrderedProducts.quantity).label('total_sold'),
        func.sum(OrderedProducts.total_price).label('total_revenue')
    ).join(
        OrderedProducts, Product.product_id == OrderedProducts.product_id
    ).group_by(
        Product.product_id, Product.item_name
    ).order_by(
        desc('total_revenue')
    ).limit(limit).all()
    
    top_products = []
    for product in product_sales:
        top_products.append({
            "product_id": product.product_id,
            "name": product.item_name,
            "sold": int(product.total_sold or 0),
            "revenue": str(product.total_revenue or 0)
        })
    
    return top_products

@router.get("/revenue-trend")
def get_revenue_trend(
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
    days: int = 30
):
    """
    Get daily revenue trend for the last N days
    """
    from datetime import date
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Get orders grouped by date
    daily_revenue = db.query(
        func.date(OrderTable.ordered_at).label('date'),
        func.sum(OrderTable.total_order_amount).label('revenue')
    ).filter(
        OrderTable.ordered_at >= start_date
    ).group_by(
        func.date(OrderTable.ordered_at)
    ).order_by(
        'date'
    ).all()
    
    # Create a complete date range with all days (filling gaps with 0)
    revenue_data = []
    current_date = start_date.date()
    revenue_dict = {row.date: float(row.revenue) for row in daily_revenue}
    
    while current_date <= end_date.date():
        revenue_data.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "revenue": revenue_dict.get(current_date, 0)
        })
        current_date += timedelta(days=1)
    
    return revenue_data

@router.get("/orders-trend")
def get_orders_trend(
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
    days: int = 30
):
    """
    Get daily order count trend for the last N days
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Get orders grouped by date
    daily_orders = db.query(
        func.date(OrderTable.ordered_at).label('date'),
        func.count(OrderTable.order_id).label('orders')
    ).filter(
        OrderTable.ordered_at >= start_date
    ).group_by(
        func.date(OrderTable.ordered_at)
    ).order_by(
        'date'
    ).all()
    
    # Create a complete date range with all days (filling gaps with 0)
    orders_data = []
    current_date = start_date.date()
    orders_dict = {row.date: int(row.orders) for row in daily_orders}
    
    while current_date <= end_date.date():
        orders_data.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "orders": orders_dict.get(current_date, 0)
        })
        current_date += timedelta(days=1)
    
    return orders_data
