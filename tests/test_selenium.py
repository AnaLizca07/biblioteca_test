from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import unittest
import requests
import json

class TestBiblioteca(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:8000"
        # Configurar el driver de Selenium
        options = webdriver.ChromeOptions()
        options.add_argument('--headless') 
        self.driver = webdriver.Chrome(options=options)
        
    def tearDown(self):
        self.driver.quit()

    # Tests de API Endpoints
    def test_get_authors(self):
        """Test GET /authors endpoint"""
        # Crear un autor de prueba
        author_data = {"name": "Gabriel García Márquez"}
        response = requests.post(f"{self.base_url}/authors", json=author_data)
        self.assertEqual(response.status_code, 201)
        
        # Obtener todos los autores
        response = requests.get(f"{self.base_url}/authors")
        self.assertEqual(response.status_code, 200)
        authors = response.json()
        self.assertTrue(any(author["name"] == "Gabriel García Márquez" for author in authors))

    def test_create_book(self):
        """Test POST /books endpoint"""
        # Crear autor primero
        author_data = {"name": "Jorge Luis Borges"}
        author_response = requests.post(f"{self.base_url}/authors", json=author_data)
        author_id = author_response.json()["id"]
        
        # Crear libro
        book_data = {
            "title": "Ficciones",
            "author_id": author_id,
            "available": True
        }
        response = requests.post(f"{self.base_url}/books", json=book_data)
        self.assertEqual(response.status_code, 201)
        book = response.json()
        self.assertEqual(book["title"], "Ficciones")
        self.assertEqual(book["author_id"], author_id)

    def test_create_and_delete_loan(self):
        """Test POST and DELETE /loans endpoints"""
        # Crear autor
        author_response = requests.post(f"{self.base_url}/authors", json={"name": "Mario Vargas Llosa"})
        author_id = author_response.json()["id"]
        
        # Crear libro
        book_data = {"title": "La ciudad y los perros", "author_id": author_id, "available": True}
        book_response = requests.post(f"{self.base_url}/books", json=book_data)
        book_id = book_response.json()["id"]
        
        # Crear préstamo
        loan_data = {"book_id": book_id, "user_name": "Juan Pérez"}
        loan_response = requests.post(f"{self.base_url}/loans", json=loan_data)
        self.assertEqual(loan_response.status_code, 201)
        loan_id = loan_response.json()["id"]
        
        # Verificar que el libro no está disponible
        book_response = requests.get(f"{self.base_url}/books/{book_id}")
        self.assertFalse(book_response.json()["available"])
        
        # Eliminar préstamo
        delete_response = requests.delete(f"{self.base_url}/loans/{loan_id}")
        self.assertEqual(delete_response.status_code, 204)
        
        # Verificar que el libro está disponible nuevamente
        book_response = requests.get(f"{self.base_url}/books/{book_id}")
        self.assertTrue(book_response.json()["available"])

    # Tests de integración con base de datos
    def test_db_author_books_relationship(self):
        """Test la relación entre autores y libros en la base de datos"""
        # Crear autor
        author_data = {"name": "Julio Cortázar"}
        author_response = requests.post(f"{self.base_url}/authors", json=author_data)
        author_id = author_response.json()["id"]
        
        # Crear varios libros del mismo autor
        books = ["Rayuela", "Bestiario"]
        created_books = []
        for title in books:
            book_data = {"title": title, "author_id": author_id, "available": True}
            response = requests.post(f"{self.base_url}/books", json=book_data)
            created_books.append(response.json())
        
        # Verificar que los libros fueron creados con el autor correcto
        self.assertEqual(len(created_books), 2)
        for book in created_books:
            self.assertEqual(book["author_id"], author_id)
            self.assertTrue(book["title"] in books)

    def test_db_book_loan_status(self):
        """Test el estado de disponibilidad de libros en la base de datos"""
        # Crear autor y libro
        author_response = requests.post(f"{self.base_url}/authors", json={"name": "Isabel Allende"})
        book_data = {
            "title": "La casa de los espíritus",
            "author_id": author_response.json()["id"],
            "available": True
        }
        book_response = requests.post(f"{self.base_url}/books", json=book_data)
        book_id = book_response.json()["id"]
        
        # Crear préstamo
        loan_data = {"book_id": book_id, "user_name": "María Rodríguez"}
        requests.post(f"{self.base_url}/loans", json=loan_data)
        
        # Verificar que el estado del libro ha cambiado en la base de datos
        book_response = requests.get(f"{self.base_url}/books/{book_id}")
        self.assertFalse(book_response.json()["available"])

    # Test end-to-end del flujo de préstamo
    def test_complete_loan_flow(self):
        """Test del flujo completo de préstamo de un libro"""
        # 1. Crear autor
        author_data = {"name": "Pablo Neruda"}
        author_response = requests.post(f"{self.base_url}/authors", json=author_data)
        author_id = author_response.json()["id"]
        
        # 2. Crear libro
        book_data = {
            "title": "Veinte poemas de amor",
            "author_id": author_id,
            "available": True
        }
        book_response = requests.post(f"{self.base_url}/books", json=book_data)
        book_id = book_response.json()["id"]
        
        # 3. Verificar disponibilidad inicial
        book_response = requests.get(f"{self.base_url}/books/{book_id}")
        self.assertTrue(book_response.json()["available"])
        
        # 4. Crear préstamo
        loan_data = {"book_id": book_id, "user_name": "Ana López"}
        loan_response = requests.post(f"{self.base_url}/loans", json=loan_data)
        self.assertEqual(loan_response.status_code, 201)
        loan_id = loan_response.json()["id"]
        
        # 5. Verificar que el libro no está disponible
        book_response = requests.get(f"{self.base_url}/books/{book_id}")
        self.assertFalse(book_response.json()["available"])
        
        # 6. Verificar préstamo en la lista de préstamos
        loans_response = requests.get(f"{self.base_url}/loans")
        self.assertTrue(any(loan["id"] == loan_id for loan in loans_response.json()))
        
        # 7. Devolver el libro (eliminar préstamo)
        delete_response = requests.delete(f"{self.base_url}/loans/{loan_id}")
        self.assertEqual(delete_response.status_code, 204)
        
        # 8. Verificar que el libro está disponible nuevamente
        book_response = requests.get(f"{self.base_url}/books/{book_id}")
        self.assertTrue(book_response.json()["available"])

if __name__ == '__main__':
    unittest.main()
