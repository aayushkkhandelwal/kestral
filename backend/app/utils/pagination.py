import math
from typing import TypeVar, List, Generic
from sqlalchemy import Select, func
from sqlalchemy.orm import Session
from app.schemas.common import PaginatedResponse

T = TypeVar("T")

def paginate_query(
    db: Session,
    select_stmt: Select,
    page: int = 1,
    page_size: int = 20
) -> PaginatedResponse[T]:
    """Applies LIMIT, OFFSET, and counts total rows efficiently."""
    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    # Total count query
    count_stmt = select_stmt.with_only_columns(func.count()).order_by(None)
    total = db.scalar(count_stmt) or 0

    # Paginated data
    offset = (page - 1) * page_size
    items = db.scalars(select_stmt.limit(page_size).offset(offset)).all()
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
