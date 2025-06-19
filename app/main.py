import os
from typing import List

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

#from . import models, schemas
#from . database import engine, get_db, Base

import models, schemas
from database import engine, get_db, Base


models.Base.metadata.create_all(bind=engine)

# Crear la app
app = FastAPI(
    title=os.getenv("APP_NAME"),
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="app"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    try:
        return FileResponse("app/index.html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "message": "API is running smoothly"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")


# --- AUTHOR ENDPOINTS ---
@app.get("/authors", response_model=List[schemas.AutorResponse], status_code=200)
def get_authors(db: Session = Depends(get_db)):
    """Obtener todos los autores"""
    authors = db.query(models.Autor).all()
    return authors

@app.get("/authors/{author_id}", response_model=schemas.AutorResponse, status_code=200)
def get_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(models.Autor).filter(models.Autor.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="No se encontró el autor")
    return author

@app.post("/authors", response_model=schemas.AutorResponse, status_code=201)
def create_author(author: schemas.AutorCreate, db: Session = Depends(get_db)):
    """Crear nuevo autor"""
    db_author = models.Autor(**author.model_dump())
    
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author

@app.delete("/authors/{author_id}", status_code=204)
def delete_author(author_id: int, db: Session = Depends(get_db)):
    """Eliminar autor"""
    author = db.query(models.Autor).filter(models.Autor.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Autor no encontrado")
    
    db.delete(author)
    db.commit()
    return None

# --- BOOK ENDPOINTS ---
@app.get("/books", response_model=List[schemas.LibroResponse])
def get_books(db: Session = Depends(get_db)):
    """Obtener todos los libros"""
    books = db.query(models.Libro).all()
    return books

@app.get("/books/{book_id}", response_model=schemas.LibroResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """Obtener libro por ID"""
    book = db.query(models.Libro).filter(models.Libro.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="No se encontró el libro")
    return book

@app.post("/books", response_model=schemas.LibroResponse, status_code=201)
def create_book(book: schemas.LibroCreate, db: Session = Depends(get_db)):
    """Crear nuevo libro"""
    author = db.query(models.Autor).filter(models.Autor.id == book.author_id).first()
    if not author:
        raise HTTPException(status_code=400, detail="No se encontró el autor")
    
    db_book = models.Libro(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """Eliminar libro"""
    book = db.query(models.Libro).filter(models.Libro.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="No se encontró el libro")
    
    db.delete(book)
    db.commit()
    return None

# --- LOAN ENDPOINTS ---
@app.get("/loans", response_model=List[schemas.PrestamoResponse])
def get_loans(db: Session = Depends(get_db)):
    """Obtener todos los préstamos"""
    loans = db.query(models.Prestamo).all()
    return loans

@app.get("/loans/{loan_id}", response_model=schemas.PrestamoResponse)
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    """Obtener préstamo por ID"""
    loan = db.query(models.Prestamo).filter(models.Prestamo.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    return loan

@app.post("/loans", response_model=schemas.PrestamoResponse, status_code=201)
def create_loan(loan: schemas.PrestamoCreate, db: Session = Depends(get_db)):
    """Crear nuevo préstamo"""
    book = db.query(models.Libro).filter(models.Libro.id == loan.book_id).first()
    if not book:
        raise HTTPException(status_code=400, detail="No se encontró el libro")
    if not book.available:
        raise HTTPException(status_code=400, detail="No está disponible el libro")
    
    db_loan = models.Prestamo(
        book_id=loan.book_id,
        user_name=loan.user_name.strip().title()
    )
    
    book.available = False
    
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    return db_loan

@app.delete("/loans/{loan_id}", status_code=204)
def delete_loan(loan_id: int, db: Session = Depends(get_db)):
    """Eliminar/devolver préstamo"""
    loan = db.query(models.Prestamo).filter(models.Prestamo.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    
    book = db.query(models.Libro).filter(models.Libro.id == loan.book_id).first()
    if book:
        book.available = True
    
    db.delete(loan)
    db.commit()
    return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)