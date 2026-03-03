"""
Script to build the SPIMI Inverted Index from the cleaned data.
"""
import time
from src.indexer.spimi import SPIMIIndexer

def main():
    print("==================================================")
    print("📦 BUILDING SPIMI INVERTED INDEX 📦")
    print("==================================================")
    
    input_file = "data/MASTER_DATA_CLEAN.jsonl"
    output_dir = "data/index"
    
    print(f"Reading from: {input_file}")
    print(f"Output directory: {output_dir}\\n")
    
    start_time = time.time()
    
    # Initialize SPIMI Indexer with 500MB memory limit per block
    indexer = SPIMIIndexer(block_size_mb=500)
    
    try:
        indexer.build_index(input_file, output_dir)
        
        elapsed = time.time() - start_time
        print(f"\\n✅ Index built successfully in {elapsed:.2f} seconds!")
        print(f"You can now run 'python run_search.py' to test the search engine.")
        
    except FileNotFoundError:
        print(f"\\n❌ Error: Input file '{input_file}' not found.")
        print("Please ensure you have run the data processing scripts first.")

if __name__ == "__main__":
    main()
