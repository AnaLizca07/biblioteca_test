Lo primero que hacemos en crear toda la estructura de carpetas
Luego crear un entorno virtual:
'''
python3 -m venv venv
'''

#Para activar en entorno virtual en Mac se ejecuta este comando:
'''
source venv/bin/activate
'''

Luego hacemos el archivo .env con las variables de entorno
Luego hacemos la sesion de la bd en database.py

Luego creamos el modelo de la bd en models.py usando sqlalchemy

Luego creamos los schemas con base en lo que querramos mostrar y las validaciones que queramos

Luego hacemos el main.py para configurar FastAPI

Se hacen las pruebas unitarias y se ejecutan con pytest tests/test_unit.py

Se hacen las pruebas de integracion y se ejecutan con pytest tests/test_integration.py

se crea el archivo de locust para hacer las pruebas de carga 
se corre con Stress test: locust --host=http://localhost:8000 --users 1000 --spawn-rate 50 --run-time 15m para prueba de estress

Para las pruebas de seguridad: 
BANDIT APP.PY MIRA LAS VULNERABILIDADES DE TEXTO PLANO
safety scan: analiza las dependencias
git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git sqlmap-dev (SQL MAP, DESCARGAR)
sqlmap -u "http://localhost:8000/authors/1" --level 3 --risk 3 --batch

para ejecutar la imagen de docker y el docker compose a la vez docker compose up

docker compose down -v  # Para limpiar todo primero
docker compose build   # Para reconstruir con los cambios del Dockerfile
docker compose up      # Para levantar los servicios
