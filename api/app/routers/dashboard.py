from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.dashboard import DashboardService
from app.schemas.dashboard import DashboardOverview
from app.models.user import User
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_model=DashboardOverview)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard overview with statistics about applications, instances, components, clusters, and environments.
    """
    return DashboardService.get_dashboard_overview(db=db)

