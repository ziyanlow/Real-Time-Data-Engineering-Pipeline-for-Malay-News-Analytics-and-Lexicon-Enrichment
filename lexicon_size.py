import redis
from pyspark.sql import SparkSession
from pyspark.sql.functions import countDistinct

class LexiconSizeAnalysis:
    def __init__(self, graph, redis_host="localhost", redis_port=6379, redis_db=0):
        self.graph = graph
        self.spark = SparkSession.builder.appName("LexiconSizeAnalysis").getOrCreate()
        
        # Initialize Redis connection
        self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
        self.redis_key = "lexicon_size"  # Key to store lexicon size in Redis
        self.redis_ttl = 60  # Cache expiration time in seconds

    def load_data(self):
        """Load unique word data from Neo4j."""
        query = """
        MATCH (w:Word)
        RETURN DISTINCT w.name AS word
        """
        return self.spark.createDataFrame(self.graph.run(query).data())

    def calculate_lexicon_size(self, df):
        """Calculate the total number of unique words in the lexicon."""
        lexicon_size = df.agg(countDistinct("word")).collect()[0][0]
        return lexicon_size

    def get_lexicon_size(self):
        """
        Retrieve lexicon size, either from Redis cache or by querying Neo4j and calculating it.
        """
        # Check if the value is in Redis
        cached_size = self.redis_client.get(self.redis_key)
        if cached_size:
            print(f"Retrieved lexicon size from Redis, total number of unique entries : {cached_size}")
            return int(cached_size)
        
        # If not in Redis, calculate it
        print("Lexicon size not found in Redis. Fetching from Neo4j...")
        data = self.load_data()
        lexicon_size = self.calculate_lexicon_size(data)
        print(f"Calculated lexicon size, total number of unique entries : {lexicon_size}")

        # Store in Redis for future use
        self.redis_client.setex(self.redis_key, self.redis_ttl, lexicon_size)
        print(f"Lexicon size cached in Redis with TTL of {self.redis_ttl} seconds.")
        return lexicon_size
