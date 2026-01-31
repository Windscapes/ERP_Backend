from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.nursery import Nursery
from app.schemas.nursery_schema import NurseryView

router = APIRouter()

@router.get("/all", response_model=list[NurseryView])
def show_all_nurseries(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    nurseries = db.query(Nursery).all()
    return [NurseryView(nursery_id=n.nursery_id, nursery_name=n.nursery_name) for n in nurseries]

@router.get("/{nursery_id}", response_model=NurseryView)
def get_nursery_by_id(
    nursery_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    nursery = db.query(Nursery).filter(Nursery.nursery_id == nursery_id).first()
    if not nursery:
        raise HTTPException(status_code=404, detail=f"Nursery with ID {nursery_id} not found")
    return NurseryView(nursery_id=nursery.nursery_id, nursery_name=nursery.nursery_name)

