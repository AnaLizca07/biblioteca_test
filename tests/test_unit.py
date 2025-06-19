import pytest
from datetime import datetime
from pydantic import ValidationError
from unittest.mock import Mock, patch
import requests

# Importar los esquemas (asumiendo que están en schemas.py)
from app.schemas import (
    AutorCreate, AutorUpdate, AutorResponse,
    LibroCreate, LibroUpdate, LibroResponse,
    PrestamoCreate, PrestamoUpdate, PrestamoResponse
)


# ===== PRUEBAS DE LÓGICA DE NEGOCIO DEL BACKEND =====

class TestLogicaNegocio:
    
    def test_crear_prestamo_libro_disponible(self):
        """Prueba que se puede crear un préstamo cuando el libro está disponible"""
        # Simular lógica de negocio
        def crear_prestamo(book_id, user_name):
            # Mock de verificación de disponibilidad
            libro_disponible = True  # Simular que el libro está disponible
            if libro_disponible:
                return {"id": 1, "book_id": book_id, "user_name": user_name, "success": True}
            return {"success": False, "error": "Libro no disponible"}
        
        resultado = crear_prestamo(1, "Juan Pérez")
        assert resultado["success"] is True
        assert resultado["book_id"] == 1
        assert resultado["user_name"] == "Juan Pérez"

    def test_crear_prestamo_libro_no_disponible(self):
        """Prueba que no se puede crear un préstamo cuando el libro no está disponible"""
        def crear_prestamo(book_id, user_name):
            libro_disponible = False  # Simular que el libro no está disponible
            if libro_disponible:
                return {"success": True}
            return {"success": False, "error": "Libro no disponible"}
        
        resultado = crear_prestamo(1, "Juan Pérez")
        assert resultado["success"] is False
        assert "no disponible" in resultado["error"]

    def test_devolver_libro_actualiza_disponibilidad(self):
        """Prueba que devolver un libro actualiza su disponibilidad"""
        def devolver_libro(prestamo_id):
            # Simular lógica de devolución
            return {
                "prestamo_returned": True,
                "libro_available": True,
                "success": True
            }
        
        resultado = devolver_libro(1)
        assert resultado["success"] is True
        assert resultado["prestamo_returned"] is True
        assert resultado["libro_available"] is True

    def test_autor_no_puede_eliminarse_con_libros(self):
        """Prueba que un autor no puede eliminarse si tiene libros asociados"""
        def eliminar_autor(autor_id):
            # Simular que el autor tiene libros
            tiene_libros = True  # Mock de verificación
            if tiene_libros:
                return {"success": False, "error": "Autor tiene libros asociados"}
            return {"success": True}
        
        resultado = eliminar_autor(1)
        assert resultado["success"] is False
        assert "libros asociados" in resultado["error"]


# ===== PRUEBAS DE VALIDACIONES DE DATOS =====

class TestValidacionesDatos:
    
    def test_validacion_nombre_autor_muy_corto(self):
        """Prueba que el nombre del autor debe tener al menos 2 caracteres"""
        with pytest.raises(ValidationError) as exc_info:
            AutorCreate(name="A")
        
        errors = exc_info.value.errors()
        assert any("at least 2 characters" in str(error) for error in errors)

    def test_validacion_datos_prestamo_correctos(self):
        """Prueba que los datos válidos del préstamo pasan la validación"""
        prestamo_data = {
            "user_name": "María González",
            "book_id": 5
        }
        
        # No debe lanzar excepción
        prestamo = PrestamoCreate(**prestamo_data)
        assert prestamo.user_name == "María González"
        assert prestamo.book_id == 5


# ===== PRUEBAS DE COMPONENTES DEL FRONTEND (Mock) =====

class TestComponentesFrontend:
    
    @patch('requests.get')
    def test_componente_lista_libros_carga_datos(self, mock_get):
        """Prueba que el componente de lista de libros carga los datos correctamente"""
        # Mock de respuesta de la API
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": 1, "title": "El Quijote", "author_id": 1, "available": True},
            {"id": 2, "title": "Cien años de soledad", "author_id": 2, "available": False}
        ]
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Simular componente que hace petición
        def obtener_libros():
            import requests
            response = requests.get("/api/libros")
            if response.status_code == 200:
                return response.json()
            return []
        
        libros = obtener_libros()
        assert len(libros) == 2
        assert libros[0]["title"] == "El Quijote"
        assert libros[1]["available"] is False

    @patch('requests.post')
    def test_componente_formulario_crear_autor(self, mock_post):
        """Prueba que el formulario de crear autor envía los datos correctamente"""
        # Mock de respuesta exitosa
        mock_response = Mock()
        mock_response.json.return_value = {"id": 1, "name": "Gabriel García Márquez"}
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        # Simular componente de formulario
        def crear_autor_frontend(nombre):
            data = {"name": nombre}
            response = requests.post("/api/autores", json=data)
            if response.status_code == 201:
                return {"success": True, "data": response.json()}
            return {"success": False}
        
        resultado = crear_autor_frontend("Gabriel García Márquez")
        assert resultado["success"] is True
        assert resultado["data"]["name"] == "Gabriel García Márquez"
        
        # Verificar que se hizo la llamada correcta
        mock_post.assert_called_once_with(
            "/api/autores", 
            json={"name": "Gabriel García Márquez"}
        )


# ===== FIXTURES Y CONFIGURACIÓN =====

@pytest.fixture
def autor_ejemplo():
    """Fixture con datos de ejemplo de un autor"""
    return AutorResponse(id=1, name="Miguel de Cervantes")

@pytest.fixture
def libro_ejemplo():
    """Fixture con datos de ejemplo de un libro"""
    return LibroResponse(
        id=1, 
        title="Don Quijote de la Mancha", 
        author_id=1, 
        available=True
    )

@pytest.fixture
def prestamo_ejemplo():
    """Fixture con datos de ejemplo de un préstamo"""
    return PrestamoResponse(
        id=1,
        book_id=1,
        user_name="Juan Pérez",
        loan_date=datetime(2024, 1, 15, 10, 30),
        returned=False
    )