"""
SPIMI (Single-Pass In-Memory Indexing) implementation.

Milestone 2: Core Search Engine
"""


class SPIMIIndexer:
    """
    Implements SPIMI algorithm for building inverted index.
    
    SPIMI Process:
    1. Split documents into blocks that fit in memory
    2. For each block: build in-memory index -> write to disk
    3. Merge all block indices into final inverted index
    """
    
    def __init__(self, block_size_mb: int = 500):
        """
        Initialize SPIMI indexer.
        
        Args:
            block_size_mb: Maximum memory per block in MB
        """
        self.block_size_mb = block_size_mb
        self.current_block = {}
        self.block_count = 0
    
    def add_document(self, doc_id: int, tokens: list[str]) -> None:
        """
        Add a document to the current block.
        
        Args:
            doc_id: Document identifier
            tokens: List of tokens from the document
        """
        # TODO: Implement document addition
        pass
    
    def write_block_to_disk(self, output_path: str) -> str:
        """
        Write current block to disk and clear memory.
        
        Args:
            output_path: Directory to save block files
            
        Returns:
            Path to the saved block file
        """
        # TODO: Implement block writing
        pass
    
    def merge_blocks(self, block_files: list[str], output_path: str) -> str:
        """
        Merge all block files into final inverted index.
        
        Args:
            block_files: List of block file paths
            output_path: Path for final index
            
        Returns:
            Path to final inverted index
        """
        # TODO: Implement n-way merge
        pass
    
    def build_index(self, documents_path: str, output_path: str) -> str:
        """
        Build complete inverted index from documents.
        
        Args:
            documents_path: Path to documents (JSONL format)
            output_path: Directory for index output
            
        Returns:
            Path to final inverted index
        """
        # TODO: Implement full indexing pipeline
        pass
