# Proyecto: Sistema de Gestión de Usuarios y Juegos

Este proyecto integra microservicios principales:  
- **users_back**: Gestión de usuarios y perfiles  
- **games_control_back**: Gestión de juegos y colecciones

## Estructura

- `/users_back`: Backend para usuarios y perfiles
- `/games_control_back`: Backend para juegos
- `init.sql`: Script de inicialización de tablas en PostgreSQL
- `mongo-init.js`: Script para inicializar la colección en MongoDB
- `docker-compose.yml`: Orquestación de servicios con Docker
- `.env`: Variables de entorno globales para los servicios

## Instalación y ejecución con Docker

1. **Configura las variables de entorno en `.env`**  
   Edita el archivo `.env` en la raíz con tus valores (usuarios, contraseñas, puertos, claves).

2. **Levanta los servicios**  
   ```bash
   docker-compose up --build
   ```

Esto iniciará:
- PostgreSQL con las tablas necesarias
- MongoDB con la colección `games`
- users_back en el puerto definido (`USERS_PORT`)
- games_control_back en el puerto definido (`GAMES_CONTROL_PORT`)

## Variables de entorno principales

```env
# PostgreSQL
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
POSTGRES_PORT

# MongoDB
MONGO_DB_NAME
MONGO_PORT
MONGO_URL
MONGO_COLLECTION_NAME

# Users Back
USERS_DATABASE_URL
USERS_PORT
ENCRYPTION_KEY

# Games Control Back
GAMES_DATABASE_URL
GAMES_CONTROL_PORT

# Compartidas
SECRET_KEY
ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
TOKEN_URL
```

## Dependencias principales

- Docker
- Docker Compose
- Python 3.11 (para desarrollo local)
- PostgreSQL
- MongoDB

---

## Ejecución local (desarrollo)

1. Instala las dependencias en cada carpeta con:
   ```bash
   pip install -r requirements.txt
   ```
2. Inicia cada servicio con:
   ```bash
   uvicorn main:app --reload --port <PUERTO>
   ```

---

Consulta los README de cada microservicio para detalles específicos.