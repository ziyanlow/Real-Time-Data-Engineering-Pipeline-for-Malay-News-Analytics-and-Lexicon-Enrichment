
from py4j.java_gateway import java_import
from pyspark.sql import SparkSession

class DataExporter:
    def __init__(self, spark_session):
        self.spark = spark_session

    def flatten_tokens(self, final_df):
        """
        Flatten the 'tokens_excluded' column in the DataFrame and return a list of tokens.
        """
        # Step 1: Flatten the tokens_excluded column
        flattened_tokens = final_df.select("tokens_excluded").rdd.flatMap(lambda row: row["tokens_excluded"]).collect()
        return flattened_tokens

    def create_tokens_df(self, flattened_tokens):
        """
        Create a new DataFrame from the flattened list of tokens.
        """
        # Step 2: Create a new DataFrame from the flattened list
        tokens_df = self.spark.createDataFrame([(token,) for token in flattened_tokens], ["token"])
        return tokens_df

    def delete_if_exists(self, output_path):
        """
        Delete the output file/directory if it exists.
        """
        # Import the Hadoop FileSystem classes
        java_import(self.spark._jvm, "org.apache.hadoop.fs.Path")
        java_import(self.spark._jvm, "org.apache.hadoop.fs.FileSystem")

        # Step 3: Define the output path and delete if it exists
        hadoop_conf = self.spark.sparkContext._jsc.hadoopConfiguration()
        fs = self.spark._jvm.org.apache.hadoop.fs.FileSystem.get(hadoop_conf)

        output_dir = self.spark._jvm.org.apache.hadoop.fs.Path(output_path)
        if fs.exists(output_dir):
            fs.delete(output_dir, True)  # True for recursive deletion of the directory
            #print(f"Output path '{output_path}' exists. Deleted it.")
        else:
            print(f"Output path '{output_path}' does not exist.")

    def export_tokens(self, tokens_df, output_path):
        """
        Write the tokens DataFrame to a single TXT file.
        """
        # Step 4: Write the tokens to a single TXT file
        tokens_df.rdd.map(lambda row: row["token"]).coalesce(1).saveAsTextFile(output_path)
        print(f"Tokens exported to {output_path}")