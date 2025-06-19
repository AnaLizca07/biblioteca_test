from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ===== ESQUEMAS AUTOR =====
class AutorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)

class AutorCreate(AutorBase):
    pass

class AutorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)

class AutorResponse(AutorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ===== ESQUEMAS LIBRO =====
class LibroBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)

class LibroCreate(LibroBase):
    author_id: int = Field(..., gt=0)

class LibroUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author_id: Optional[int] = Field(None, gt=0)
    available: Optional[bool] = None

class LibroResponse(LibroBase):
    id: int
    author_id: int
    available: bool
    model_config = ConfigDict(from_attributes=True)

# ===== ESQUEMAS PRÉSTAMO =====
class PrestamoBase(BaseModel):
    user_name: str = Field(..., min_length=2, max_length=100)

class PrestamoCreate(PrestamoBase):
    book_id: int = Field(..., gt=0)

class PrestamoUpdate(BaseModel):
    returned: Optional[bool] = None

class PrestamoResponse(PrestamoBase):
    id: int
    book_id: int
    loan_date: datetime
    returned: bool
    model_config = ConfigDict(from_attributes=True)

# ===== ESQUEMAS CON RELACIONES =====
class LibroConAutor(LibroResponse):
    author: Optional[AutorResponse] = None

class AutorConLibros(AutorResponse):
    books: List[LibroResponse] = []

class PrestamoCompleto(PrestamoResponse):
    book: Optional[LibroResponse] = None