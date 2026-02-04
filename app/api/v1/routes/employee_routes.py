from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.deps import get_db, get_current_user, require_admin
from app.models.user import UserTable
from app.models.employee_scan_log import EmployeeScanLog
from app.models.order_table import OrderTable
from app.schemas.employee_schema import EmployeeCreateRequest, EmployeeCreateResponse
from app.core.security import hash_password
from app.core.id_generator import generate_user_id
from sqlalchemy import func

router = APIRouter()


@router.post("/create", response_model=EmployeeCreateResponse)
def create_employee(
    payload: EmployeeCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(require_admin)
):
    """Create a new employee account"""
    # Check if username already exists
    existing = db.query(UserTable).filter(UserTable.user_username == payload.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    
    # Generate employee ID
    employee_id = generate_user_id(db, "employee")
    
    # Create new employee
    new_employee = UserTable(
        user_id=employee_id,
        user_username=payload.username,
        user_password=hash_password(payload.password),
        role="employee"
    )
    
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    
    return EmployeeCreateResponse(
        employee_id=new_employee.user_id,
        username=new_employee.user_username,
        message="Employee created successfully"
    )


@router.get("/employees")
def get_all_employees(
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(require_admin)
):
    """Get all employees with their statistics"""
    employees = db.query(UserTable).filter(UserTable.role == "employee").all()
    
    result = []
    for emp in employees:
        # Get scan logs count
        scans_count = db.query(func.count(EmployeeScanLog.scan_id)).filter(
            EmployeeScanLog.employee_id == emp.user_id
        ).scalar() or 0
        
        # Get completed orders count (orders that this employee worked on and are completed)
        completed_orders = db.query(func.count(func.distinct(EmployeeScanLog.order_id))).join(
            OrderTable, EmployeeScanLog.order_id == OrderTable.order_id
        ).filter(
            EmployeeScanLog.employee_id == emp.user_id,
            OrderTable.status == "COMPLETED"
        ).scalar() or 0
        
        result.append({
            "employee_id": emp.user_id,
            "username": emp.user_username,
            "role": emp.role,
            "created_at": emp.created_at,
            "items_scanned": scans_count,
            "orders_completed": completed_orders,
            "status": "active"  # You can add a status field to UserTable if needed
        })
    
    return result


@router.get("/employees/{employee_id}")
def get_employee_detail(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(require_admin)
):
    """Get detailed information about a specific employee"""
    employee = db.query(UserTable).filter(
        UserTable.user_id == employee_id,
        UserTable.role == "employee"
    ).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get scan logs count
    scans_count = db.query(func.count(EmployeeScanLog.scan_id)).filter(
        EmployeeScanLog.employee_id == employee.user_id
    ).scalar() or 0
    
    # Get completed orders count
    completed_orders = db.query(func.count(func.distinct(EmployeeScanLog.order_id))).join(
        OrderTable, EmployeeScanLog.order_id == OrderTable.order_id
    ).filter(
        EmployeeScanLog.employee_id == employee.user_id,
        OrderTable.status == "COMPLETED"
    ).scalar() or 0
    
    # Get recent scan logs
    recent_scans = db.query(EmployeeScanLog).filter(
        EmployeeScanLog.employee_id == employee.user_id
    ).order_by(EmployeeScanLog.scanned_at.desc()).limit(10).all()
    
    return {
        "employee_id": employee.user_id,
        "username": employee.user_username,
        "role": employee.role,
        "created_at": employee.created_at,
        "items_scanned": scans_count,
        "orders_completed": completed_orders,
        "status": "active",
        "recent_scans": [
            {
                "scan_id": log.scan_id,
                "order_id": log.order_id,
                "product_id": log.product_id,
                "scanned_quantity": log.scanned_quantity,
                "scanned_at": log.scanned_at
            }
            for log in recent_scans
        ]
    }
