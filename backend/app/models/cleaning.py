from typing import Optional
from enum import Enum
from app.models.core import IDModelMixin, CoreModel

class CleaningType(str, Enum):
    dust_up = "dust_up"
    spot_clean = "spot_clean"
    full_clean = "full_clean"


# 자원의 모든 공유 속성
class CleaningBase(CoreModel):
    """
    All common characteristics of our Cleaning resource
    """
    name: Optional[str]
    description: Optional[str]
    price: Optional[float]
    cleaning_type: Optional[CleaningType] = "spot_clean"


# 새 리소스를 만드는 데 필요한 속성 (POST)
class CleaningCreate(CleaningBase):
    name: str
    price: float


# 업데이트할 수 있는 속성 (PUT)
class CleaningUpdate(CleaningBase):
    cleaning_type: Optional[cleaningType]


# 데이터베이스에서 나오는 모든 리소스에 있는 속성
class CleaningInDB(IDModelMixin, CleaningBase):
    name: str
    price: float
    cleaning_type: CleaningType


# GET, POST, PUT 요청에서 반환되는 공개 대상 리소스에 있는 속성
class CleaningPublic(IDModelMixin, CleaningBase):
    pass
