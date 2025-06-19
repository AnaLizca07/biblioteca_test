import pytest
import os 
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.models import Autor, Libro, Prestamo
from app.main import app

# Base de datos de prueba con postgresql
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Crear el cliente de pruebas UNA VEZ
client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    """Configurar DB limpia para cada test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_author(db_session):
    """Crear un autor de ejemplo para las pruebas"""
    autor = Autor(name="Gabriel García Márquez")  # Usar 'name' en lugar de 'nombre'
    db_session.add(autor)
    db_session.commit()
    db_session.refresh(autor)
    return autor

@pytest.fixture
def sample_book(db_session, sample_author):
    """Crear un libro de ejemplo para las pruebas"""
    libro = Libro(
        title="Cien años de soledad", 
        author_id=sample_author.id, 
        available=True
    )
    db_session.add(libro)
    db_session.commit()
    db_session.refresh(libro)
    return libro


class TestIntegracionBD:

    def test_crear_autor(self, db_session):
        """Test básico de creación de autor en BD"""
        autor = Autor(name="Gabriel García Márquez")  # Cambiar 'nombre' por 'name'
        db_session.add(autor)
        db_session.commit()
        db_session.refresh(autor)

        assert autor.id is not None
        assert autor.name == "Gabriel García Márquez"  # Cambiar 'nombre' por 'name'

    def test_crear_libro(self, db_session):
        """Test básico de creación de libro en BD"""
        autor = Autor(name="Gabriel García Márquez")  # Cambiar 'nombre' por 'name'
        db_session.add(autor)
        db_session.commit()
        db_session.refresh(autor)

        libro = Libro(title="Cien años de soledad", author_id=autor.id, available=True)  # Cambiar nombres de campos
        db_session.add(libro)
        db_session.commit()
        db_session.refresh(libro)

        assert libro.id is not None
        assert libro.title == "Cien años de soledad"  # Cambiar 'titulo' por 'title'
        assert libro.author_id == autor.id  # Cambiar 'autor_id' por 'author_id'
        assert libro.available is True  # Cambiar 'disponible' por 'available'

    def test_crear_prestamo(self, db_session, sample_book):
        """Test básico de creación de préstamo en BD"""
        prestamo = Prestamo(
            book_id=sample_book.id,
            user_name="Juan Pérez"
        )
        db_session.add(prestamo)
        db_session.commit()
        db_session.refresh(prestamo)

        assert prestamo.id is not None
        assert prestamo.book_id == sample_book.id
        assert prestamo.user_name == "Juan Pérez"
        assert prestamo.returned is False
        assert prestamo.loan_date is not None


# ===== 3 PRUEBAS DE ENDPOINTS DE LA API =====

class TestEndpointsAPI:

    def test_endpoint_crear_autor(self, db_session):
        """Test del endpoint POST /authors"""
        author_data = {
            "name": "Isabel Allende"  # Cambiar 'nombre' por 'name'
        }
        
        response = client.post("/authors", json=author_data)  # Usar 'client' en lugar de 'TestClient'
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Isabel Allende"  # Cambiar 'nombre' por 'name'
        assert "id" in data
        
        # Verificar que se guardó en la BD
        autor_bd = db_session.query(Autor).filter(Autor.name == "Isabel Allende").first()  # Corregir 'nameo' por 'name'
        assert autor_bd is not None

    def test_endpoint_obtener_libros(self, db_session, sample_author):
        """Test del endpoint GET /books"""
        # Crear algunos libros en la BD
        libro1 = Libro(title="El amor en los tiempos del cólera", author_id=sample_author.id, available=True)
        libro2 = Libro(title="Crónica de una muerte anunciada", author_id=sample_author.id, available=False)
        
        db_session.add_all([libro1, libro2])
        db_session.commit()
        
        response = client.get("/books")  # Usar 'client' en lugar de 'TestClient'
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] in ["El amor en los tiempos del cólera", "Crónica de una muerte anunciada"]
        assert data[1]["title"] in ["El amor en los tiempos del cólera", "Crónica de una muerte anunciada"]

    def test_endpoint_crear_prestamo_libro_no_disponible(self, db_session, sample_author):
        """Test del endpoint POST /loans con libro no disponible"""
        # Crear un libro no disponible
        libro = Libro(title="Libro prestado", author_id=sample_author.id, available=False)
        db_session.add(libro)
        db_session.commit()
        db_session.refresh(libro)
        
        loan_data = {
            "book_id": libro.id,
            "user_name": "María López"
        }
        
        response = client.post("/loans", json=loan_data)  # Usar 'client' en lugar de 'TestClient'
        
        assert response.status_code == 400
        assert "No está disponible el libro" in response.json()["detail"]


# ===== 1 PRUEBA END-TO-END DEL FLUJO COMPLETO DE PRÉSTAMO =====

class TestFlujoPrestamo:

    def test_flujo_completo_prestamo(self, db_session):
        """
        Test end-to-end completo del flujo de préstamo:
        1. Crear autor
        2. Crear libro (disponible)
        3. Crear préstamo (libro se marca como no disponible)
        4. Verificar estado del préstamo
        5. Devolver libro (eliminar préstamo, libro disponible nuevamente)
        """
        
        # PASO 1: Crear autor
        author_data = {"name": "Mario Vargas Llosa"}
        response = client.post("/authors", json=author_data)  # Usar 'client' en lugar de 'TestClient'
        assert response.status_code == 201
        author_id = response.json()["id"]
        
        # PASO 2: Crear libro disponible
        book_data = {
            "title": "La ciudad y los perros",
            "author_id": author_id
        }
        response = client.post("/books", json=book_data)
        assert response.status_code == 201
        book_data_response = response.json()
        book_id = book_data_response["id"]
        assert book_data_response["available"] is True  # Libro inicialmente disponible
        
        # PASO 3: Crear préstamo (libro debe marcarse como no disponible)
        loan_data = {
            "book_id": book_id,
            "user_name": "ana garcia"  # Lowercase para probar transformación
        }
        response = client.post("/loans", json=loan_data)
        assert response.status_code == 201
        loan_data_response = response.json()
        loan_id = loan_data_response["id"]
        assert loan_data_response["user_name"] == "Ana Garcia"  # Verificar transformación a Title Case
        assert loan_data_response["returned"] is False
        
        # PASO 4: Verificar que el libro ya no está disponible
        response = client.get(f"/books/{book_id}")
        assert response.status_code == 200
        book_after_loan = response.json()
        assert book_after_loan["available"] is False  # Libro no disponible después del préstamo
        
        # PASO 5: Verificar estado del préstamo
        response = client.get(f"/loans/{loan_id}")
        assert response.status_code == 200
        loan_status = response.json()
        assert loan_status["book_id"] == book_id
        assert loan_status["user_name"] == "Ana Garcia"
        assert loan_status["returned"] is False
        
        # PASO 6: Devolver libro (eliminar préstamo)
        response = client.delete(f"/loans/{loan_id}")
        assert response.status_code == 204
        
        # PASO 7: Verificar que el libro está disponible nuevamente
        response = client.get(f"/books/{book_id}")
        assert response.status_code == 200
        book_after_return = response.json()
        assert book_after_return["available"] is True  # Libro disponible después de devolución
        
        # PASO 8: Verificar que el préstamo ya no existe
        response = client.get(f"/loans/{loan_id}")
        assert response.status_code == 404
        
        # PASO 9: Verificar que se puede crear un nuevo préstamo del mismo libro
        new_loan_data = {
            "book_id": book_id,
            "user_name": "Carlos Mendoza"
        }
        response = client.post("/loans", json=new_loan_data)
        assert response.status_code == 201
        new_loan_response = response.json()
        assert new_loan_response["user_name"] == "Carlos Mendoza"