from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int = 1
    pages: Optional[int] = None

    def model_post_init(self, __context):
        if self.pages is not None:
            self.total_pages = self.pages
        elif self.page_size > 0:
            self.total_pages = (self.total + self.page_size - 1) // self.page_size
            self.pages = self.total_pages

    model_config = ConfigDict(from_attributes=True)

class MessageResponse(BaseModel):
    message: str
    status: str = "success"
