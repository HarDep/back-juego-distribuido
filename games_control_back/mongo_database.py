from pymongo import MongoClient
from pymongo.database import Database, Collection
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("MONGO_DB_NAME")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME")

class MongoDBManager:
    def __init__(self):
        self.client: MongoClient | None = None
        self.db : Database | None = None
        self.collection : Collection | None = None

    def connect(self):
        self.client = MongoClient(MONGO_URL)
        self.db = self.client[DB_NAME]

    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.collection = None

    def get_collection(self) -> Collection:
        if self.collection:
            return self.collection
        return self.db[COLLECTION_NAME]

db_mongo_manager = MongoDBManager()