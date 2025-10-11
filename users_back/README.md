# users_back

Microservicio para la gestión de usuarios y perfiles.  
Incluye registro, login, consulta y actualización de perfiles y contraseñas.

## Instalación

### Requisitos
- Python 3.11+
- PostgreSQL
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
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ENCRYPTION_KEY=1234567890abcdef1234567890abcdef
   TOKEN_URL=http://localhost:8000/api/v1/auth/token
   ```
3. Inicia el servidor:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Instalación con Docker

1. Asegúrate de tener configurado el archivo `.env` en la raíz del proyecto.
2. Construye y ejecuta el contenedor:
   ```bash
   docker build -t users_back .
   docker run --env-file ../.env -p 8000:8000 users_back
   ```

## Variables de entorno

- `DATABASE_URL`: URL de conexión a PostgreSQL
- `SECRET_KEY`: Clave secreta para JWT
- `ALGORITHM`: Algoritmo JWT
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Minutos de expiración del token
- `ENCRYPTION_KEY`: Clave para cifrado AES (16, 24 o 32 bytes)
- `TOKEN_URL`: URL para obtener el token

## Dependencias principales

- fastapi
- uvicorn[standard]
- SQLAlchemy
- python-dotenv
- python-jose[cryptography]
- passlib[bcrypt]
- cryptography
- psycopg2-binary
- pydantic
- python-multipart
---