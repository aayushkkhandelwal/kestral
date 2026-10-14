import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_optional_current_user, require_permission
from app.models.user import User
from app.schemas.video import VideoResponse, VideoDetailResponse, VideoFilter, VideoTaskStatusResponse
from app.schemas.common import PaginatedResponse
from app.services.video_service import VideoService

router = APIRouter(tags=["Videos"])


@router.post("/upload-video", status_code=status.HTTP_202_ACCEPTED)
async def upload_video(
    file: UploadFile = File(...),
    camera_id: uuid.UUID | None = None,
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
    background_tasks: BackgroundTasks = None
):
    service = VideoService(db)
    return await service.process_upload(
        file=file,
        camera_id=camera_id,
        current_user=current_user,
        background_tasks=background_tasks
    )


@router.get("/videos", response_model=PaginatedResponse[VideoResponse])
def list_videos(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    camera_id: uuid.UUID | None = None,
    status: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20
):
    service = VideoService(db)
    filters = VideoFilter(
        camera_id=camera_id,
        status=status,
        search=search,
        page=page,
        page_size=page_size
    )
    items, total = service.list_videos(filters, current_user=current_user)
    pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    return PaginatedResponse(
        items=[VideoResponse.model_validate(v) for v in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/video/{video_id}", response_model=VideoDetailResponse)
def get_video(
    video_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)]
):
    service = VideoService(db)
    return service.get_by_id(video_id)


@router.delete("/video/{video_id}", status_code=status.HTTP_200_OK)
def delete_video(
    video_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_permission("videos:delete"))],
    db: Annotated[Session, Depends(get_db)]
):
    service = VideoService(db)
    service.delete_video(video_id, current_user=current_user)
    return {"message": "Video deleted successfully", "video_id": str(video_id)}


@router.get("/tasks/{task_id}/status", response_model=VideoTaskStatusResponse)
def get_task_status(
    task_id: str,
    db: Annotated[Session, Depends(get_db)]
):
    service = VideoService(db)
    return service.get_task_status(task_id)


@router.get("/tasks/{task_id}/results")
def get_task_results(
    task_id: str,
    db: Annotated[Session, Depends(get_db)]
):
    service = VideoService(db)
    return service.get_task_results(task_id)
