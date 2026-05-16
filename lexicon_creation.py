from pyspark.sql import SparkSession
from pymongo import MongoClient
from bson import ObjectId

class HDFSToMongoDB:
    def __init__(self, hdfs_path, mongo_uri, db_name, collection_name, object_id):
        self.hdfs_path = hdfs_path
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.object_id = ObjectId(object_id)
        self.spark = None

    def initialize_spark(self):
        """Initialize the Spark session."""
        self.spark = SparkSession.builder.appName("ImportTXTtoMongoDBArray").getOrCreate()

    def read_txt_file(self):
        """Read the TXT file from HDFS into an RDD."""
        lines_rdd = self.spark.sparkContext.textFile(self.hdfs_path)
        return lines_rdd.collect()

    def connect_to_mongodb(self):
        """Connect to MongoDB and return the specified collection."""
        client = MongoClient(self.mongo_uri)
        db = client[self.db_name]
        return db[self.collection_name]

    def update_mongodb(self, tokens_array):
        """Overwrite the tokens field in the existing document in MongoDB."""
        collection = self.connect_to_mongodb()
        result = collection.update_one(
            {"_id": self.object_id},
            {"$set": {"tokens": tokens_array}},  # Overwrite tokens with the new array
            upsert=True
        )

        if result.matched_count > 0:
            return "Tokens overwritten in the existing document in MongoDB!"
        elif result.upserted_id:
            return f"Document with ObjectId {self.object_id} created."
        else:
            return f"Document with ObjectId {self.object_id} not found and no changes were made."

    def filter_tokens(self, tokens_array):
        """Filter out duplicate tokens based on the 'word' field."""
        collection = self.connect_to_mongodb()
        existing_document = collection.find_one({"_id": self.object_id})

        existing_words = set()
        if existing_document and "tokens" in existing_document:
            existing_words = set(token['word'] for token in existing_document["tokens"] if 'word' in token)

        # Filter out duplicates
        new_tokens = [token for token in tokens_array if token not in existing_words]
        return new_tokens

    def append_mongodb(self, tokens_array):
        """Append new tokens to the existing document's tokens field."""
        collection = self.connect_to_mongodb()
        new_tokens = self.filter_tokens(tokens_array)

        if not new_tokens:
            return "No new tokens to append; all tokens are duplicates."

        result = collection.update_one(
            {"_id": self.object_id},
            {"$push": {"tokens": {"$each": new_tokens}}},
            upsert=True
        )

        if result.matched_count > 0:
            return f"Added {len(new_tokens)} new tokens to the existing document in MongoDB!"
        elif result.upserted_id:
            return f"Document with ObjectId {self.object_id} was not found, but a new document was created with this ObjectId."
        else:
            return "Document not found and no changes were made."

    def stop_spark(self):
        """Stop the Spark session."""
        if self.spark:
            self.spark.stop()
