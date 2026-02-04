from pydantic import BaseModel, Field

class EmployeeCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

class EmployeeCreateResponse(BaseModel):
    employee_id: str
    username: str
    message: str

class EmployeeResponse(BaseModel):
    employee_id: str
    username: str
    role: str
    created_at: str
    items_scanned: int
    orders_completed: int
    status: str
    
    class Config:
        from_attributes = True
