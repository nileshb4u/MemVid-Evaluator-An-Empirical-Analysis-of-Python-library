# memvid-evaluator/config.py

import os

# --- Directory Paths ---
# Get the absolute path of the directory where this config.py file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define paths relative to the base directory
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_DOCS_DIR = os.path.join(DATA_DIR, "input_docs")
MEMVID_OUTPUT_DIR = os.path.join(DATA_DIR, "memvid_output")
RESULTS_DIR = os.path.join(DATA_DIR, "results")
LOGS_DIR = os.path.join(BASE_DIR, "logs") # Optional: if you add file logging

# Ensure these directories exist
os.makedirs(INPUT_DOCS_DIR, exist_ok=True)
os.makedirs(MEMVID_OUTPUT_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
# os.makedirs(LOGS_DIR, exist_ok=True) # Uncomment if you add file logging

# --- MemVid Parameters ---
DEFAULT_MEMVID_CHUNK_SIZE_KB = 100  # Default chunk size in KB for memvid encoding

# --- Benchmarking Parameters ---
DEFAULT_BENCHMARK_RESULTS_FILE = os.path.join(RESULTS_DIR, "benchmarks.csv")

# --- Preprocessing Parameters ---
# Add any relevant config for preprocessing if needed, e.g., max text length to process

# --- UI / Streamlit ---
# Add any UI related constants if needed

# --- Logging --- # Optional for now
LOG_LEVEL = "INFO" # e.g., DEBUG, INFO, WARNING, ERROR

if __name__ == '__main__':
    # A simple test to print out the configured paths when the script is run directly
    print(f"Base Directory: {BASE_DIR}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Input Docs Directory: {INPUT_DOCS_DIR}")
    print(f"MemVid Output Directory: {MEMVID_OUTPUT_DIR}")
    print(f"Results Directory: {RESULTS_DIR}")
    print(f"Default Benchmark Results File: {DEFAULT_BENCHMARK_RESULTS_FILE}")
    print(f"Default MemVid Chunk Size (KB): {DEFAULT_MEMVID_CHUNK_SIZE_KB}")