from pyspark.sql.functions import col, lower, regexp_replace, trim

class DataCleaner:
    def clean_data(self, df):
        # Cleaning steps applied to the provided DataFrame
        cleaned_df = df \
            .withColumn("value", regexp_replace(col("value"), "URL:\\s*http[s]?://\\S+|www\\.\\S+", "")) \
            .withColumn("value", lower(col("value"))) \
            .withColumn("value", regexp_replace(col("value"), r"\b(title|content)\b", "")) \
            .withColumn("value", regexp_replace(col("value"), "[^a-zA-Z\\s-]", "")) \
            .withColumn("value", regexp_replace(col("value"), r"(?<![a-zA-Z])-|-(?![a-zA-Z])", "")) \
            .withColumn("value", regexp_replace(col("value"), "\\s+", " ")) \
            .withColumn("value", trim(col("value"))) \
            .filter((col("value") != "") & (col("value").isNotNull()))
        return cleaned_df

    def format_data(self, cleaned_df):
        # Combine lines into single rows based on empty lines
        def combine_lines(lines):
            current_row = []
            for line in lines:
                if line.strip():  # Non-empty line
                    current_row.append(line.strip())
                else:  # Empty line indicates end of a record
                    if current_row:
                        yield ' '.join(current_row)
                    current_row = []
            if current_row:  # Yield the last record if any
                yield ' '.join(current_row)

        # Convert DataFrame to RDD and process it
        cleaned_rdd = cleaned_df.rdd.map(lambda row: row['value'])
        formatted_rdd = cleaned_rdd.mapPartitions(combine_lines)
        formatted_df = formatted_rdd.map(lambda x: (x,)).toDF(["combined_text"])
        return formatted_df

