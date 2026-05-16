from py2neo import Graph, Node, Relationship
import pandas as pd

class Neo4jImporter:
    def __init__(self, uri, user, password):
        """Initialize the Neo4jImporter with connection details."""
        self.uri = uri
        self.user = user
        self.password = password
        self.graph = None

    def connect(self):
        """Connect to the Neo4j database."""
        try:
            self.graph = Graph(self.uri, auth=(self.user, self.password))
            if self.graph:
                print("Connection to Neo4j established successfully!")
            else:
                print("Failed to establish a connection to Neo4j.")
        except Exception as e:
            print(f"Error connecting to Neo4j: {e}")

    def is_valid(self, value):
        """Check if a field is valid."""
        return value and str(value).strip().lower() != "tiada maklumat"

    def store_data(self, spark_df):
        """Store data into Neo4j."""
        if self.graph is None:
            raise ValueError("Graph connection not established. Call connect() before attempting to store data.")

        # Convert Spark DataFrame to Pandas DataFrame
        data = spark_df.toPandas()

        for _, row in data.iterrows():
            # Create the main "Word" node
            word_node = Node(
                "Word",
                name=row["Word"],
                definition=row["Definitions"],
                part_of_speech=row["Part of Speech"],
                sentiment_score=row["Sentiment_Score"],
                sentimental_label=row["Sentimental_Label"],
            )
            self.graph.merge(word_node, "Word", "name")  # Ensure no duplicate Words

            # Create relationships for each column
            self.create_relationship(word_node, "Stemmed Word", row["Stemmed Word"], "Stemmed Word", "HAS_STEMMED_WORD")
            self.create_relationship(word_node, "Contexts", row["Contexts"], "Context", "HAS_CONTEXT")
            self.create_relationship(word_node, "Synonyms", row["Synonyms"], "Synonym", "HAS_SYNONYM")
            self.create_relationship(word_node, "Antonyms", row["Antonyms"], "Antonym", "HAS_ANTONYM")
            self.create_relationship(word_node, "Derived Words", row["Derived Words"], "DerivedWord", "HAS_DERIVED_WORD")
            self.create_relationship(word_node, "Hypernyms", row["Hypernyms"], "Hypernym", "HAS_HYPERNYM")
            self.create_relationship(word_node, "Hyponyms", row["Hyponyms"], "Hyponym", "HAS_HYPONYM")
            self.create_relationship(word_node, "Meronyms", row["Meronyms"], "Meronym", "HAS_MERONYM")
            self.create_relationship(word_node, "Holonyms", row["Holonyms"], "Holonym", "HAS_HOLONYM")

        print("Data import successful!")

    def create_relationship(self, word_node, column_name, column_value, node_label, relationship_type):
        """
        Create relationships for the Word node based on a column's data.

        :param word_node: The Word node to connect.
        :param column_name: Name of the column being processed.
        :param column_value: Value of the column for the current row.
        :param node_label: Label for the related nodes.
        :param relationship_type: Type of relationship to establish.
        """
        if self.is_valid(column_value):
            values = str(column_value).split(";")
            for value in values:
                related_node = Node(node_label, name=value.strip())
                self.graph.merge(related_node, node_label, "name")
                self.graph.merge(Relationship(word_node, relationship_type, related_node))