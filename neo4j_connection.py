# neo4j_connection.py
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from py2neo import Graph
import logging

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.graph = None

    def connect_neo4j_driver(self):
        """Initialize the connection using the official Neo4j driver."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            print("Neo4j Driver Connection: Connection successful!")
        except ServiceUnavailable:
            print("Neo4j Driver: Unable to connect. Please check the server status and configuration.")
        except Exception as e:
            print(f"Neo4j Driver: An unexpected error occurred: {e}")

    def connect_py2neo(self):
        """Initialize the connection using the py2neo library."""
        try:
            self.graph = Graph(self.uri, auth=(self.user, self.password))
            print("py2neo Connection: Connection successful!")
        except ServiceUnavailable:
            print("py2neo: Unable to connect. Please check the server status and configuration.")
        except Exception as e:
            print(f"py2neo: An unexpected error occurred: {e}")
    
    def test_connection_driver(self):
        """Test the connection using the Neo4j driver."""
        if self.driver:
            try:
                with self.driver.session() as session:
                    greeting = session.run("RETURN 'Connection successful!' AS message").single()["message"]
                    print(f"Neo4j Driver Connection: {greeting}")
            except ServiceUnavailable:
                print("Neo4j Driver: Unable to connect. Please check the server status and configuration.")
            except Exception as e:
                print(f"Neo4j Driver: An unexpected error occurred: {e}")

    def test_connection_py2neo(self):
        """Test the connection using the py2neo library."""
        if self.graph:
            try:
                # Using .data() method to fetch the result
                result = self.graph.run("RETURN 'Connection successful!' AS message").data()
                print(f"py2neo Connection: {result[0]['message']}")
            except ServiceUnavailable:
                print("py2neo: Unable to connect. Please check the server status and configuration.")
            except Exception as e:
                print(f"py2neo: An unexpected error occurred: {e}")
    
    def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            print("Neo4j Driver connection closed.")
