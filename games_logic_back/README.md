# games_logic_back

Microservicio para la gestión de logica de juegos. Utiliza

## Requisitos

- Python 3.x
- Las siguientes dependencias:
  - `aiohttp`
  - `asyncio`
  - `bson`
  - `motor`
  - `pydantic`
  - `socketio`
  - `SQLAlchemy`

## Instalación local

1. Clona este repositorio en tu máquina local.
2. Navega al directorio `games_logic_back`.
3. Crea un entorno virtual (opcional, pero se recomienda).
4. Ejecuta `pip install -r requirements.txt` para instalar las dependencias.
5. Configura las variables de entorno necesarias en un archivo `.env` en la raíz del proyecto. Puedes utilizar el archivo `.env.example` como referencia.
6. Ejecuta `python main.py` para iniciar el servidor.

## Instalación con Docker

1. Asegúrate de tener Docker instalado en tu máquina.
2. Navega al directorio raíz del proyecto.
3. Asegúrate de tener configurado el archivo `.env` en la raíz del proyecto.
4. Construye y ejecuta el contenedor:
    ```bash
   docker build -t games_logic_back .
   docker run --env-file ../.env -p 8002:8002 games_control_back
   ```

## Variables de entorno

Las siguientes variables de entorno se pueden configurar en el archivo `.env` o en el archivo `docker-compose.yml`:

- `MONGO_URL`: URL de conexión a la base de datos MongoDB.
- `MONGO_DB_NAME`: Nombre de la base de datos MongoDB.
- `MONGO_COLLECTION_NAME`: Nombre de la colección de MongoDB.

## Dependencias

Las siguientes dependencias se utilizan en este proyecto:

- `aiohttp`: Biblioteca para trabajar con HTTP en Python.
- `asyncio`: Biblioteca para trabajar con programación asíncrona en Python.
- `pydantic`: Biblioteca para definir y validar modelos de datos en Python.
- `socketio`: Biblioteca para trabajar con Socket.IO en Python.
- `pymongo`: Biblioteca para trabajar con MongoDB en Python.
