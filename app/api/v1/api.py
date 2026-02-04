from fastapi import APIRouter

from app.api.v1.routes.auth_routes import router as auth_router
from app.api.v1.routes.product_routes import router as product_router
from app.api.v1.routes.order_routes import router as order_router
from app.api.v1.routes.order_read_routes import router as order_read_router
from app.api.v1.routes.product_read_routes import router as product_read_router
from app.api.v1.routes.nursery_routes import router as nursery_router
from app.api.v1.routes.order_status_routes import router as order_status_router
from app.api.v1.routes.analytics_routes import router as analytics_router
from app.api.v1.routes.employee_routes import router as employee_router
from app.api.v1.routes.notification_routes import router as notification_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])

api_router.include_router(product_router, prefix="/products", tags=["Products Write"])
api_router.include_router(product_read_router, prefix="/products", tags=["Products Read"])

api_router.include_router(order_router, prefix="/orders", tags=["Orders Write"])
api_router.include_router(order_read_router, prefix="/orders", tags=["Orders Read"])

api_router.include_router(order_status_router, prefix="/orders", tags=["Order Status"])

api_router.include_router(nursery_router, prefix="/nursery", tags=["Nursery"])

api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])

api_router.include_router(employee_router, prefix="/employees", tags=["Employees"])

api_router.include_router(notification_router, prefix="/notifications", tags=["Notifications"])
