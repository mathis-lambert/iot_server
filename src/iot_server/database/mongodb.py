from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError


class MongoDB:
    def __init__(
            self,
            host: str,
            port: int,
            username: str,
            password: str,
            db_name: str,
            collection_name: str
    ):
        """
        Initialise la connexion à MongoDB.
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        self.connect()

    def connect(self):
        try:
            self.client = MongoClient(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                serverSelectionTimeoutMS=5000
            )
            # Test de la connexion
            self.client.server_info()
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            print(f"[MongoDB] Connected to {self.host}:{self.port} ({self.db_name}.{self.collection_name})")
        except ConnectionFailure as e:
            print(f"[MongoDB] Connection failed: {e}")
            raise

    def insert_one(self, document: dict):
        """
        Insère un document dans la collection.
        """
        try:
            result = self.collection.insert_one(document)
            return result.inserted_id
        except PyMongoError as e:
            print(f"[MongoDB] insert_one error: {e}")
            return None

    def find_one(self, query: dict):
        """
        Trouve un document correspondant à la requête.
        """
        try:
            return self.collection.find_one(query)
        except PyMongoError as e:
            print(f"[MongoDB] find_one error: {e}")
            return None

    def find(self, query: dict = {}, limit: int = 0):
        """
        Retourne les documents correspondant à la requête (avec limite optionnelle).
        """
        try:
            cursor = self.collection.find(query)
            if limit:
                cursor = cursor.limit(limit)
            return list(cursor)
        except PyMongoError as e:
            print(f"[MongoDB] find error: {e}")
            return []

    def update_one(self, query: dict, update: dict, upsert: bool = False):
        """
        Met à jour un document correspondant à la requête.
        """
        try:
            result = self.collection.update_one(query, {'$set': update}, upsert=upsert)
            return result.modified_count
        except PyMongoError as e:
            print(f"[MongoDB] update_one error: {e}")
            return 0

    def delete_one(self, query: dict):
        """
        Supprime un document correspondant à la requête.
        """
        try:
            result = self.collection.delete_one(query)
            return result.deleted_count
        except PyMongoError as e:
            print(f"[MongoDB] delete_one error: {e}")
            return 0

    def close(self):
        """
        Ferme la connexion à MongoDB.
        """
        if self.client:
            self.client.close()
            print("[MongoDB] Connection closed.")
