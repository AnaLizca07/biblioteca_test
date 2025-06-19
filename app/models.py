from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
#from .database import Base
from database import Base

class Autor(Base):
    __tablename__ = "autores"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    #relacion 
    books = relationship("Libro", back_populates="author")

class Libro(Base):
    __tablename__ = "libros"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("autores.id"))
    available = Column(Boolean, default=True)
    
    author = relationship("Autor", back_populates="books")
    loans = relationship("Prestamo", back_populates="book")

class Prestamo(Base):
    __tablename__ = "prestamos"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("libros.id"))
    user_name = Column(String, nullable=False)
    loan_date = Column(DateTime, default=datetime.utcnow)
    returned = Column(Boolean, default=False)
    
    # Relación
    book = relationship("Libro", back_populates="loans")

