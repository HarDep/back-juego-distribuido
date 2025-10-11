# games_control_back

Microservicio para la gestión de juegos y colecciones.  
Utiliza PostgreSQL y MongoDB para almacenar información de juegos.

## Instalación

### Requisitos
- Python 3.11+
- PostgreSQL
- MongoDB
- (Opcional) Docker

### Instalación local

1. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Configura las variables de entorno en `.env`:
   ```
   DATABASE_URL=postgresql://postgres:password@localhost:5432/mydb
   SECRET_KEY=...
   ALGORITHM=HS256
   MONGO_URL=mongodb://localhost:27017
   MONGO_DB_NAME=gameDB
   MONGO_COLLECTION_NAME=games
   TOKEN_URL=http://localhost:8000/api/v1/auth/token
   ```
3. Inicia el servidor:
   ```bash
   uvicorn main:app --reload --port 8001
   ```

### Instalación con Docker

1. Asegúrate de tener configurado el archivo `.env` en la raíz del proyecto.
2. Construye y ejecuta el contenedor:
   ```bash
   docker build -t games_control_back .
   docker run --env-file ../.env -p 8001:8001 games_control_back
   ```

## Variables de entorno

- `DATABASE_URL`: URL de conexión a PostgreSQL
- `SECRET_KEY`: Clave secreta para JWT
- `ALGORITHM`: Algoritmo JWT
- `MONGO_URL`: URL de conexión a MongoDB
- `MONGO_DB_NAME`: Nombre de la base de datos MongoDB
- `MONGO_COLLECTION_NAME`: Nombre de la colección MongoDB
- `TOKEN_URL`: URL para obtener el token

## Dependencias principales

- fastapi
- uvicorn[standard]
- pymongo
- SQLAlchemy
- python-dotenv
- python-jose[cryptography]
- psycopg2-binary
- pydantic
- dnspython

---
