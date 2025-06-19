from locust import HttpUser, task, between, events
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LibraryUser(HttpUser):
    """
    - Stress test: locust --host=http://localhost:8000 --users 1000 --spawn-rate 50 --run-time 15m
    """
    
    wait_time = between(1, 3)  # Users wait 1-3 seconds between tasks
    
    # Store IDs for created resources
    author_ids = []
    book_ids = []
    loan_ids = []

    def on_start(self):
        """Initialize test data on startup"""
        try:
            # Create initial test data
            self.create_initial_author()
            if self.author_ids:
                self.create_initial_book()
        except Exception as e:
            logger.error(f"Failed to create initial data: {str(e)}")

    def create_initial_author(self):
        """Create an initial author for testing"""
        name = f"Test Author {random.randint(1, 1000)}"
        with self.client.post("/authors", json={"name": name}, catch_response=True) as response:
            if response.status_code == 201:
                author_id = response.json()["id"]
                self.author_ids.append(author_id)
                logger.info(f"Created initial author with ID: {author_id}")
            else:
                logger.error(f"Failed to create initial author: {response.text}")

    def create_initial_book(self):
        """Create an initial book for testing"""
        if not self.author_ids:
            return
            
        title = f"Test Book {random.randint(1, 1000)}"
        author_id = random.choice(self.author_ids)
        
        with self.client.post("/books", json={
            "title": title,
            "author_id": author_id
        }, catch_response=True) as response:
            if response.status_code == 201:
                book_id = response.json()["id"]
                self.book_ids.append(book_id)
                logger.info(f"Created initial book with ID: {book_id}")
            else:
                logger.error(f"Failed to create initial book: {response.text}")

    @task(3)
    def get_all_authors(self):
        """GET /authors - List all authors"""
        with self.client.get("/authors", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get authors: {response.text}")

    @task(2)
    def create_author(self):
        """POST /authors - Create a new author"""
        name = f"Author {random.randint(1, 100000)}"
        with self.client.post("/authors", json={"name": name}, catch_response=True) as response:
            if response.status_code == 201:
                self.author_ids.append(response.json()["id"])
            else:
                response.failure(f"Failed to create author: {response.text}")

    @task(3)
    def get_all_books(self):
        """GET /books - List all books"""
        with self.client.get("/books", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Failed to get books: {response.text}")

    @task(2)
    def create_book(self):
        """POST /books - Create a new book"""
        if not self.author_ids:
            return
            
        author_id = random.choice(self.author_ids)
        title = f"Book {random.randint(1, 100000)}"
        
        with self.client.post("/books", json={
            "title": title,
            "author_id": author_id
        }, catch_response=True) as response:
            if response.status_code == 201:
                self.book_ids.append(response.json()["id"])
            else:
                response.failure(f"Failed to create book: {response.text}")

    @task(2)
    def create_loan(self):
        """POST /loans - Create a new loan"""
        if not self.book_ids:
            return
            
        book_id = random.choice(self.book_ids)
        user_name = f"User {random.randint(1, 100000)}"
        
        with self.client.post("/loans", json={
            "book_id": book_id,
            "user_name": user_name
        }, catch_response=True) as response:
            if response.status_code == 201:
                self.loan_ids.append(response.json()["id"])
            else:
                response.failure(f"Failed to create loan: {response.text}")

    @task(1)
    def return_book(self):
        """DELETE /loans/{id} - Return a book"""
        if not self.loan_ids:
            return
            
        loan_id = random.choice(self.loan_ids)
        with self.client.delete(f"/loans/{loan_id}", catch_response=True) as response:
            if response.status_code == 204:
                self.loan_ids.remove(loan_id)
            else:
                response.failure(f"Failed to return book: {response.text}")

    @task(1)
    def health_check(self):
        """GET /health - Check API health"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Health check failed: {response.text}")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Called when a test is starting
    """
    logger.info("Load test is starting")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Called when a test is ending
    """
    logger.info("Load test is ending")
