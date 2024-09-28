from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from uuid import uuid4
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchIndex,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
)
from search_backend import config

class Indexer:
    """
    A class to handle the indexing of PDF page embeddings into Azure Cognitive Search.

    This class manages the creation of search indexes, preparation of documents,
    ingestion of embeddings, and verification of document indexing within Azure Cognitive Search.
    """

    def __init__(self, pdf_page_data):
        """
        Initializes the Indexer with PDF page data and sets up Azure Search clients.

        Args:
            pdf_page_data (list): A list of dictionaries containing PDF name, page number, content, and embedding.
        """
        self.pdf_page_data = pdf_page_data
        self.index_client = SearchIndexClient(
            endpoint=config.COGNITIVE_SEARCH_CONFIG["endpoint"],
            credential=AzureKeyCredential(config.COGNITIVE_SEARCH_CONFIG["api_key"])
        )
        self.search_client = SearchClient(
            endpoint=config.COGNITIVE_SEARCH_CONFIG["endpoint"],
            index_name=config.COGNITIVE_SEARCH_CONFIG["index_name"],
            credential=AzureKeyCredential(config.COGNITIVE_SEARCH_CONFIG["api_key"])
        )

    def does_index_exist(self):
        """
        Checks if the specified search index exists in Azure Cognitive Search.

        Returns:
            bool: True if the index exists, False otherwise.
        """
        try:
            index_names = list(self.index_client.list_index_names())
            return config.COGNITIVE_SEARCH_CONFIG["index_name"] in index_names
        except Exception as e:
            config.app_logger.error(f"Error checking index existence: {str(e)}")
            return False

    def create_index(self):
        """
        Creates a search index in Azure Cognitive Search if it does not already exist.

        The index includes fields for PDF ID, PDF name, page number, embedding vector, and page content.
        It also configures vector search capabilities using the HNSW algorithm.
        """
        if not self.does_index_exist():
            try:
                fields = [
                    SimpleField(
                        name="id",
                        type=SearchFieldDataType.String,
                        key=True,
                        filterable=True,
                        sortable=True
                    ),
                    SearchableField(
                        name="pdf_name",
                        type=SearchFieldDataType.String,
                        searchable=True,
                        filterable=True,
                        sortable=True
                    ),
                    SearchField(
                        name="page_number",
                        type=SearchFieldDataType.Int32,
                        filterable=True,
                        sortable=True
                    ),
                    SearchField(
                        name="pdf_vector",
                        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        searchable=True,
                        vector_search_dimensions=config.EMBEDDING_DIMENSION,
                        vector_search_profile_name="default_vector_search_profile",
                    ),
                    SearchableField(
                        name="content",
                        type=SearchFieldDataType.String,
                        searchable=True
                    )
                ]

                search_index = SearchIndex(
                    name=config.COGNITIVE_SEARCH_CONFIG["index_name"],
                    fields=fields,
                    vector_search=VectorSearch(
                        profiles=[
                            VectorSearchProfile(
                                name="default_vector_search_profile",
                                algorithm_configuration_name="default_hnsw_algorithm_config"
                            )
                        ],
                        algorithms=[
                            HnswAlgorithmConfiguration(
                                name="default_hnsw_algorithm_config",
                            )
                        ]
                    )
                )
                self.index_client.create_index(search_index)
                config.app_logger.info("Search Index is created successfully!")
            except Exception as e:
                config.app_logger.error(f"Error creating index: {str(e)}")
        else:
            config.app_logger.info("Index already exists. Skipping index creation.")

    def prepare_document(self, pdf_name, page_number, embedding, content):
        """
        Prepares a document dictionary for indexing into Azure Cognitive Search.

        Args:
            pdf_name (str): The name of the PDF file.
            page_number (int): The page number of the PDF.
            embedding (list): The embedding vector representing the PDF page.
            content (str): The cleaned content of the PDF page.

        Returns:
            dict or None: A dictionary representing the document ready for indexing,
                          or None if an error occurs.
        """
        try:
            if len(embedding) != config.EMBEDDING_DIMENSION:
                raise ValueError(
                    f"Embedding dimension mismatch: Expected {config.EMBEDDING_DIMENSION}, got {len(embedding)}"
                )

            document = {
                "id": str(uuid4()),
                "pdf_name": pdf_name,
                "page_number": page_number,
                "pdf_vector": embedding,
                "content": content
            }
            return document
        except Exception as e:
            config.app_logger.error(f"Error preparing document for {pdf_name}, page {page_number}: {str(e)}")
            return None

    def ingest_embeddings(self):
        """
        Ingests all PDF page embeddings into Azure Cognitive Search.

        This method performs the following steps:
            1. Creates the search index if it does not exist.
            2. Iterates through all PDF page embeddings.
            3. Prepares and uploads new documents to the search index.

        Logs the outcome of the ingestion process.
        """
        # Create the index if it does not exist
        self.create_index()

        documents = []
        for page_data in self.pdf_page_data:
            pdf_name = page_data['pdf_name']
            page_number = page_data['page_number']
            embedding = page_data['embedding']
            content = page_data['content']

            # Prepare and collect document for indexing
            document = self.prepare_document(pdf_name, page_number, embedding, content)
            if document:
                documents.append(document)

        if documents:
            try:
                self.search_client.upload_documents(documents=documents)
                config.app_logger.info(f"{len(documents)} documents indexed successfully!")
            except Exception as e:
                config.app_logger.error(f"Error during document ingestion: {str(e)}")
        else:
            config.app_logger.info("No documents to index.")
