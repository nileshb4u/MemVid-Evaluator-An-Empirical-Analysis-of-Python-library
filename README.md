# memvid-evaluator/README.md

# MemVid Evaluator

This project aims to empirically evaluate the `memvid` library (https://pypi.org/project/memvid/) for its performance in encoding text data into video format and decoding it back. The evaluation focuses on storage efficiency, processing speed, and accuracy, particularly in contexts relevant to information retrieval systems.

## Features

-   Upload various document types (TXT, PDF, DOCX) for testing.
-   Benchmark `memvid` encoding and decoding processes.
-   Analyze storage size implications (original vs. `memvid` vs. gzipped text).
-   Verify accuracy of the encoding/decoding process.
-   Visualize results using a Streamlit web interface.

## Project Structure
memvid-evaluator/
├── app.py                     # Main Streamlit app, orchestrator
├── memvid_interface.py        # Wrapper for memvid library
├── preprocessor.py            # Text extraction from documents
├── benchmark_utils.py         # Benchmarking logic and orchestration
├── config.py                  # Optional: for configurations
├── pages/                     # For multi-page Streamlit views
│   └── 1_📊_Results_Dashboard.py # Page for displaying aggregated results/charts
├── data/
│   ├── input_docs/            # Sample documents for testing (PDF, TXT, DOCX)
│   ├── memvid_output/         # Stores generated .mp4 and _metadata.json files
│   └── results/               # Stores benchmark_data.csv, analysis_summary.json etc.
├── logs/                      # Optional: for log files
│   └── evaluator.log
├── tests/                     # Optional: for unit tests (e.g., for preprocessor, interface wrappers)
│   ├── test_preprocessor.py
│   └── test_memvid_interface.py
├── requirements.txt
└── README.md

## Setup

1.  **Clone the repository (or create project manually):**
    ```bash
    # If you have a git repo for this evaluator:
    # git clone <your-evaluator-repo-url>
    # cd memvid-evaluator
    # Otherwise, just ensure you are in your memvid-evaluator directory
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv venv
    # On macOS/Linux
    source venv/bin/activate
    # On Windows
    # venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Prepare Test Data:**
    Place some sample `.txt`, `.pdf`, and `.docx` files into the `data/input_docs/` directory.

## Usage

Run the Streamlit application:

```bash
streamlit run app.py
Use code with caution.
Then open your web browser to the URL provided by Streamlit (usually http://localhost:8501).
**Next Steps:**

Now we'll start creating the Python modules. Let's begin with the simpler ones and build up.

1.  `config.py` (even if very simple initially)
2.  `preprocessor.py`
3.  `memvid_interface.py`
4.  `benchmark_utils.py`
5.  `app.py` (main Streamlit app)
6.  `pages/1_📊_Results_Dashboard.py`