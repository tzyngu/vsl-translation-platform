from fastapi import APIRouter, Depends

from core.models import TrainingJob
from ..security import current_user
from ..utils import serialize


router = APIRouter(prefix="/training", tags=["training"])


def job_dict(job: TrainingJob) -> dict:
    return serialize({
        "_id": job.pk, "user_id": job.user_id, "status": job.status, "message": job.message,
        "created_at": job.created_at, "started_at": job.started_at, "finished_at": job.finished_at,
    })


@router.get("/jobs")
def list_jobs(user=Depends(current_user)):
    return [job_dict(item) for item in TrainingJob.objects.filter(user=user).order_by("-created_at")]


@router.post("/jobs")
def create_job(user=Depends(current_user)):
    job = TrainingJob.objects.create(
        user=user, status="pending", message="Queued for Phase 2 worker integration (Celery + Redis)."
    )
    return job_dict(job)

