This project provides a framework and tools to empirically evaluate the MemVid library (version 0.2.x), particularly its core functionalities for encoding textual data into a video format (reportedly using QR codes) and subsequently retrieving that text. Our evaluation focuses on:

Storage Efficiency: Comparing MemVid's storage footprint against original and compressed text.
Processing Speed: Measuring encoding and decoding times.
Data Transformation & Fidelity: Understanding how MemVid processes input text and the accuracy of retrieval.
The MemVid library itself (v0.2.x) appears to be a more comprehensive AI Memory system with features for LLM integration and semantic search. This evaluator primarily focuses on the foundational text-to-video encoding and retrieval aspects (MemvidEncoder and MemvidRetriever) as a baseline performance study.

🚀 Features of this Evaluator
Automated Benchmarking: A script (run_all_experiments.py) to systematically test multiple files with various MemVid encoding parameters (codecs, Docker usage).
Interactive Application: A Streamlit web application (app.py) for:
Uploading individual documents (TXT, PDF, DOCX).
Manually configuring encoding parameters.
Running benchmarks on single files.
Viewing detailed metrics for individual runs.
Results Dashboard: An integrated Streamlit page (pages/1_📊_Results_Dashboard.py) to visualize and filter aggregated benchmark results from CSV output.
Modular Codebase:
preprocessor.py: For text extraction.
memvid_interface.py: A dedicated wrapper for interacting with the MemVid library.
benchmark_utils.py: Handles the core logic of running benchmarks and collecting metrics.
Data-Driven Analysis: Generates a detailed CSV (benchmarks.csv) of all collected metrics, suitable for further analysis and research.
❓ Key Research Questions Addressed
This evaluator aims to gather data to help answer questions like:

How does MemVid's storage requirement for text compare to raw text and standard gzipped text?
What are the encoding and decoding speeds when using MemVid with different text sizes and codecs?
Does the text retrieved via MemVid match the original input text byte-for-byte, or does the encoding process introduce transformations?
How do parameters like video codec or the use of Docker for encoding influence MemVid's performance?
🛠️ Setup and Installation
Follow these steps to set up and run the MemVid Evaluator:

Prerequisites:

Python 3.9+
pip (Python package installer)
git (for cloning the repository)
For python-magic-bin (file type detection):
Windows: python-magic-bin usually includes necessary binaries.
Linux (Ubuntu/Debian): sudo apt-get install libmagic1
macOS (Homebrew): brew install libmagic
For MemVid's h265/h264 Codecs (Optional, if testing these):
Native FFmpeg: If you want to run MemvidEncoder with enable_docker=False for these codecs, you need a working FFmpeg installation accessible in your system's PATH.
Docker: If you want to run MemvidEncoder with enable_docker=True (recommended for consistent FFmpeg environment for advanced codecs), ensure Docker Desktop or Docker daemon is installed and running. MemVid might attempt to pull/use an FFmpeg Docker image.
Installation Steps:

Clone the Repository:

git clone https://github.com/your-username/memvid-evaluator.git 
# Replace with your actual repository URL
cd memvid-evaluator
Create and Activate a Python Virtual Environment:

python -m venv venv
On macOS/Linux:
source venv/bin/activate
On Windows (Command Prompt):
venv\Scripts\activate.bat
On Windows (PowerShell):
venv\Scripts\Activate.ps1
# If you get an error, you might need to run: Set-ExecutionPolicy Unrestricted -Scope Process
Install Dependencies:

pip install -r requirements.txt
Prepare Input Documents (Optional for Initial Run):

The repository includes a few small example documents in data/input_docs/.
To conduct thorough experiments, place your own test documents (TXT, PDF, DOCX) into the data/input_docs/ directory.
🚀 Usage
There are two main ways to use the MemVid Evaluator:

1. Automated Batch Testing
This is recommended for systematic experiments across multiple files and parameters.

Configure run_all_experiments.py:
Open run_all_experiments.py in a text editor.
Modify the CODECS_TO_TEST list (e.g., ['mp4v', 'h265', 'h264']).
Modify DOCKER_SETTINGS_TO_TEST (e.g., [False, True]).
Run the script:
python run_all_experiments.py
Output:
The script will print progress to the console for each run.
A timestamped CSV file (e.g., automated_benchmarks_YYYYMMDD_HHMMSS.csv) containing all collected metrics will be saved in the data/results/ directory.
Sanity checks on the generated CSV will be printed to the console.
Generated videos and index files will be stored in data/memvid_output/ (these are not automatically cleaned by this script).
2. Interactive Testing & Dashboard (Streamlit App)
This is useful for testing individual files, exploring parameters, and visualizing results.

Run the Streamlit application:
streamlit run app.py
Open the URL provided by Streamlit (usually http://localhost:8501) in your web browser.
Using the "App" page (main page):
Upload a document (TXT, PDF, DOCX) using the sidebar.
Select "Encoder Codec" and "Use Docker for Encoder" settings in the sidebar.
Click "🚀 Run Benchmark".
View the detailed metrics for that single run displayed on the page.
Generated files (.mp4, _index.json) are saved in data/memvid_output/.
Results are appended to data/results/benchmarks.csv.
Use the "Advanced: Clear Output Data" options in the sidebar to clean up generated files if needed.
Using the "📊 Results Dashboard" page (accessible from sidebar navigation):
This page loads data from data/results/benchmarks.csv.
Use the sidebar filters (Filename, Codec, Docker, Accuracy) to explore the data.
View aggregated statistics and interactive charts (Storage Ratios, Processing Times, Actual Sizes).
Download the filtered data as a CSV.
📁 Project Structure
memvid-evaluator/ ├── .gitignore # Files and directories to ignore in git ├── LICENSE # Project license (e.g., MIT) ├── README.md # This file ├── requirements.txt # Python dependencies ├── config.py # Configuration for paths, default parameters ├── preprocessor.py # Text extraction from TXT, PDF, DOCX ├── memvid_interface.py # Wrapper for MemVid library (Encoder & Retriever) ├── benchmark_utils.py # Core benchmarking logic and CSV saving ├── run_all_experiments.py # Script for automated batch experiments ├── app.py # Main Streamlit application (single file tests) ├── pages/ # Streamlit multi-page directory │ └── 1_📊_Results_Dashboard.py # Streamlit page for results visualization ├── data/ │ ├── input_docs/ # Place your test documents here (examples provided) │ │ ├── example_doc.txt │ │ └── .gitkeep │ ├── results/ # Benchmark output CSVs are saved here │ │ ├── example_benchmarks.csv # Example output │ │ └── .gitkeep │ └── memvid_output/ # Generated videos and index files (gitignored) │ └── .gitkeep

📜 Interpreting Benchmark Results
The primary output is the benchmarks.csv file (and its visualization on the dashboard). Key columns include:

original_text_size_bytes: Size of your input text after preprocessing.
gzipped_text_size_bytes: Size of input text after gzip compression (a common baseline).
total_memvid_storage_bytes: Sum of MemVid's video and index file. Compare this to original/gzipped.
decoded_canonical_text_size_bytes: Size of the text as reconstructed from MemVid. Compare to original_text_size_bytes to see transformation.
encoding_time_seconds, decoding_full_time_seconds: Performance metrics.
accuracy_check_input_vs_decoded_passed: True if the SHA256 of the (stripped) input text matches the SHA256 of the (stripped) decoded canonical text. Often False due to MemVid's internal text processing.
error_message: Any errors encountered during a specific run.
⚠️ Limitations
This evaluator focuses on the fundamental text encoding/decoding storage and speed characteristics of MemVid (v0.2.x) using MemvidEncoder.add_text() and MemvidRetriever. It does not evaluate the library's more advanced AI/RAG features like semantic search quality or LLM integration performance.
Performance metrics (speed, file sizes with certain codecs) can be hardware and OS dependent.
The internal workings of MemVid's QR code generation, video composition, and indexing are treated as a black box.
The text extraction from PDFs and DOCX files by preprocessor.py is standard but may not perfectly capture all text from highly complex layouts.
🤝 Contributing
Suggestions and bug reports are welcome via GitHub Issues.
Feel free to fork and extend for your own research.
📄 License
This project is licensed under the [MIT License]. See the LICENSE file for details.

🙏 Acknowledgments
This project evaluates the MemVid library. Thanks to its authors (Olow304/memvid)for providing the tool.
Thanks to PYPI.org for hositng library https://pypi.org/project/memvid
Built using Python, Streamlit, Pandas, Altair, and other open-source libraries.
