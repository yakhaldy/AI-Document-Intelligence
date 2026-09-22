from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import User
from src.api.auth import require_admin
from src.api.deps import get_db
from src.api.schemas import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


def _to_out(user: User) -> UserOut:
    return UserOut(id=user.id, username=user.username, role=user.role, status=user.status)


@router.get("/users", response_model=list[UserOut])
def list_users(
    status_: str | None = Query(default=None, alias="status"),
    session: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    stmt = select(User).order_by(User.created_at.desc())
    if status_:
        stmt = stmt.where(User.status == status_)
    users = session.execute(stmt).scalars().all()
    return [_to_out(u) for u in users]


def _set_status(user_id: int, new_status: str, session: Session) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Compte introuvable")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Impossible de modifier le statut d'un administrateur")
    user.status = new_status
    session.commit()
    return user


@router.post("/users/{user_id}/approve", response_model=UserOut)
def approve_user(user_id: int, session: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return _to_out(_set_status(user_id, "approved", session))


@router.post("/users/{user_id}/reject", response_model=UserOut)
def reject_user(user_id: int, session: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return _to_out(_set_status(user_id, "rejected", session))
