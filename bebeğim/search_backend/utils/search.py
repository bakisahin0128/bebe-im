from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
import config

class AISearcher:
    """
    A class to handle searching for the most relevant PDF pages using Azure Cognitive Search.

    This class connects to an Azure Cognitive Search index containing PDF page embeddings and provides
    functionality to search for the most similar PDF pages based on a provided question embedding vector.
    """

    def __init__(self):
        """
        Initializes the AISearcher by setting up the Azure SearchClient.

        The SearchClient is configured using the endpoint, index name, and API key provided
        in the configuration.
        """
        self.search_client = SearchClient(
            endpoint=config.COGNITIVE_SEARCH_CONFIG["endpoint"],
            index_name=config.COGNITIVE_SEARCH_CONFIG["index_name"],
            credential=AzureKeyCredential(config.COGNITIVE_SEARCH_CONFIG["api_key"])
        )

    def search_similar_pdf_pages(self, question_embedding, top_k=10):
        """
        Searches for the most similar PDF pages based on the provided question embedding.

        This method performs a vector search against the "pdf_vector" field in the Azure Cognitive Search index.
        It retrieves the top_k PDF pages that are closest to the provided question embedding vector.

        Args:
            question_embedding (list): The embedding vector for the question text.
            top_k (int, optional): The number of top similar PDF pages to return. Defaults to 10.

        Returns:
            list: A list of dictionaries, each containing the PDF name, page number, content, and similarity score.
                  Returns an empty list if an error occurs during the search.
        """
        try:
            # Create a VectorizedQuery to search for similar vectors in the "pdf_vector" field
            vector_query = VectorizedQuery(
                vector=question_embedding,
                k_nearest_neighbors=top_k,
                fields="pdf_vector",
                exhaustive=True  # Set to True for exact nearest neighbor search
            )

            # Perform the search on the indexed PDF page vectors
            search_results = self.search_client.search(
                search_text="*",  # Wildcard to include all documents, prioritize vector search
                vector_queries=[vector_query],
                select=["pdf_name", "page_number", "content"],  # Include pdf_name, page_number, and content in the results
                top=top_k
            )

            # Process the search results and compile the top PDF pages with their similarity scores
            results = []
            for result in search_results:
                results.append({
                    "pdf_name": result["pdf_name"],
                    "page_number": result["page_number"],
                    "content": result.get("content", "N/A"),  # Default to "N/A" if content is missing
                    "similarity_score": result["@search.score"]  # Retrieve the similarity score from the search metadata
                })

            return results

        except Exception as e:
            # Log any exceptions that occur during the search process
            config.app_logger.error(f"Error during search for similar PDF pages: {str(e)}")
            return []
