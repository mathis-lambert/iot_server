from typing import Optional, List, Dict, Any

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

from iot_server.settings import settings


class MongoDB:
    def __init__(
            self,
            host: str,
            port: int,
            username: str,
            password: str,
            db_name: str,
            collection_name: str,
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
                serverSelectionTimeoutMS=5000,
            )
            # Test de la connexion
            self.client.server_info()
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            print(
                f"[MongoDB] Connected to {self.host}:{self.port} ({self.db_name}.{self.collection_name})"
            )
        except ConnectionFailure as e:
            print(f"[MongoDB] Connection failed: {e}")
            raise

    def aggregate(self, pipeline: list, **kwargs):
        """
        Exécute un aggregation pipeline MongoDB.

        :param pipeline: Liste des étapes d'agrégation.
        :param kwargs: Arguments supplémentaires (ex: allowDiskUse=True).
        :return: Générateur de documents résultat ou une liste, selon l'utilisation.
        """
        try:
            cursor = self.collection.aggregate(pipeline, **kwargs)
            return list(cursor)  # tu peux retourner un itérable si tu veux
        except PyMongoError as e:
            print(f"[MongoDB] aggregate error: {e}")
            return []

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

    def find_one(
            self,
            query: Dict[str, Any],
            filter: Optional[Dict[str, int]] = None,
            **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Trouve un document correspondant à la requête.

        :param query: Dictionnaire de filtre MongoDB.
        :param filter: Projection des champs (ex: {"field1": 1, "field2": 0}).
        :param kwargs: Arguments supplémentaires pour pymongo.find_one.
        :return: Document trouvé ou None.
        """
        try:
            return self.collection.find_one(query, projection=filter, **kwargs)
        except PyMongoError as e:
            print(f"[MongoDB] find_one error: {e}")
            return None

    def find(
            self,
            query: Dict[str, Any] = {},
            filter: Optional[Dict[str, int]] = None,
            limit: int = 0,
            **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Retourne les documents correspondant à la requête (avec limite optionnelle).

        :param query: Dictionnaire de filtre MongoDB.
        :param filter: Projection des champs.
        :param limit: Nombre maximum de documents à retourner (0 = pas de limite).
        :param kwargs: Arguments supplémentaires pour pymongo.find.
        :return: Liste de documents.
        """
        try:
            cursor = self.collection.find(query, projection=filter, **kwargs)
            if limit > 0:
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
            result = self.collection.update_one(query, {"$set": update}, upsert=upsert)
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


mongo_client = MongoDB(
    settings.mongo_host,
    settings.mongo_port,
    settings.mongo_username,
    settings.mongo_password,
    "iot",
    "events",
)
