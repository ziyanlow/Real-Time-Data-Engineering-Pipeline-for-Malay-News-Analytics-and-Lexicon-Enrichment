from pyspark.ml.feature import Tokenizer
from pyspark.sql.functions import udf, col
from pyspark.sql.types import ArrayType, StringType
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
import nltk

class DataProcessor:
    def __init__(self):
        nltk.download('words')
        self.english_words = set(nltk.corpus.words.words())

        factory = StopWordRemoverFactory()
        self.stopword_remover = factory.create_stop_word_remover()

    @staticmethod
    def remove_duplicates(tokens):
        seen = set()
        return [token for token in tokens if token not in seen and not seen.add(token)]

    def remove_malay_stopwords(self, tokens):
        return [token for token in tokens if self.stopword_remover.remove(token) != token]

    def exclude_tokens(self, tokens, filtered_tokens):
        filtered_set = set(filtered_tokens)
        return [token for token in tokens if token not in filtered_set]

    def exclude_english_words(self, tokens, filtered_tokens):
        filtered_set = set(filtered_tokens)
        return [token for token in tokens if token.lower() not in self.english_words and token not in filtered_set]

    def process_data(self, formatted_df):
        tokenizer = Tokenizer(inputCol="combined_text", outputCol="tokens")
        tokenized_df = tokenizer.transform(formatted_df)

        remove_duplicates_udf = udf(self.remove_duplicates, ArrayType(StringType()))
        tokenized_df = tokenized_df.withColumn("deduplicated_tokens", remove_duplicates_udf("tokens"))

        remove_stopwords_udf = udf(self.remove_malay_stopwords, ArrayType(StringType()))
        df_without_stopwords = tokenized_df.withColumn("filtered_tokens", remove_stopwords_udf("deduplicated_tokens"))

        exclude_tokens_udf = udf(self.exclude_tokens, ArrayType(StringType()))
        minus_df = df_without_stopwords.withColumn(
            "minus_tokens", exclude_tokens_udf(col("tokens"), col("filtered_tokens"))
        )

        exclude_english_words_udf = udf(self.exclude_english_words, ArrayType(StringType()))
        final_df = df_without_stopwords.withColumn(
            "tokens_excluded", exclude_english_words_udf(col("deduplicated_tokens"), col("filtered_tokens"))
        )

        return final_df, tokenized_df, df_without_stopwords, minus_df
