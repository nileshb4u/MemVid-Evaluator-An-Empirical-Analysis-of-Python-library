memvid-evaluator System Architecture
The system is designed as a single, locally runnable application with a web interface (Streamlit) for ease of use and visualization, and a clear separation of concerns in the backend Python modules.
I. Core Components & Modules:
Presentation Layer (Web UI):
Technology: Streamlit
File: app.py (main dashboard/controller), pages/*.py (for additional views if needed, e.g., detailed results dashboard).
Responsibilities:
Provide a user interface for file uploads.
Display configuration options for benchmarking (e.g., memvid chunk size if varied).
Trigger the benchmarking process.
Present results: summary statistics, tables, charts.
Allow downloading of generated files (e.g., memvid video, metadata, results CSV).
Display logs or status updates during processing.
Application Logic / Orchestration Layer:
File: Primarily within app.py (Streamlit callbacks/functions triggered by UI interactions).
Responsibilities:
Handle uploaded files.
Coordinate calls to the Preprocessor, MemVidInterface, and BenchmarkRunner.
Manage the flow of data between components.
Format data for display in the UI.
Manage session state if needed (e.g., to hold results of current run).
Service Layer (Core Functionality):
3.1. Preprocessor Module:
File: preprocessor.py
Responsibilities:
Accept an input file path or file-like object.
Identify file type (TXT, PDF, DOCX) using python-magic or file extension.
Implement specific parsing logic for each supported file type to extract raw text content.
parse_txt(file_object) -> str
parse_pdf(file_object) -> str (using pypdf2 or pdfminer.six)
parse_docx(file_object) -> str (using python-docx)
Return the extracted text as a string.
Handle potential parsing errors gracefully.
3.2. MemVidInterface Module:
File: memvid_interface.py
Responsibilities:
Act as a wrapper around the memvid PyPI library.
encode_text_to_memvid(text_content: str, output_video_basename: str, memvid_params: dict) -> (video_path: str, metadata_path: str):
Takes raw text and memvid specific parameters (e.g., chunk_size_kb).
Constructs the output paths for video and metadata files (e.g., in data/memvid_output/).
Calls the memvid library's encoding functions.
Returns paths to the generated video and metadata files.
decode_memvid_to_text(video_path: str) -> str:
Takes the path to a memvid video.
Calls the memvid library's full decoding function.
Returns the decoded text.
decode_memvid_chunk_to_text(video_path: str, chunk_index: int) -> str:
Calls memvid to decode a specific chunk.
Returns the text content of that chunk.
get_memvid_metadata_info(video_path: str) -> dict:
Loads a memvid video and extracts relevant metadata (e.g., number of chunks, encoding parameters used).
Handle errors from the memvid library.
3.3. BenchmarkRunner Module:
File: benchmark_utils.py (could be renamed benchmark_runner.py)
Responsibilities:
Orchestrate the benchmarking for a given input text or file.
run_full_benchmark(original_file_path: str, text_content: str, memvid_params: dict) -> dict:
Calculate original text size.
Calculate gzipped text size (using gzip module).
Time the MemVidInterface.encode_text_to_memvid call.
Get resulting video and metadata file paths.
Calculate video and metadata file sizes.
Time the MemVidInterface.decode_memvid_to_text call (full decode).
If chunked decoding is relevant and memvid supports it efficiently:
Get number of chunks from metadata.
Time MemVidInterface.decode_memvid_chunk_to_text for a sample chunk (e.g., first, middle, last or random). This needs careful design for meaningful results.
Verify accuracy (e.g., hash original text vs. fully decoded text).
Compile all metrics into a structured dictionary.
Store individual benchmark results (e.g., append to a CSV file in data/results/).
Data Layer (Storage & Management):
Directory: data/
Responsibilities:
data/input_docs/: Store the curated set of input documents for testing.
data/memvid_output/: Store the generated memvid video files (.mp4) and their corresponding metadata files (_metadata.json).
data/results/: Store structured benchmark results (e.g., benchmarks.csv, analysis_summary.json).
File System: No database is used; all data is file-based.
Utilities / Shared Components:
Logging: Standard Python logging module configured to output to console and optionally a file (e.g., logs/evaluator.log).
Configuration: Simple configuration (e.g., default memvid chunk size, output paths) might be at the top of app.py or in a separate config.py.
Error Handling: Consistent error handling and reporting throughout the modules.
II. Data Flow & Interactions (Example: Single File Benchmark):
User Interaction (UI - app.py):
User uploads document.pdf via Streamlit file uploader.
User clicks "Run Benchmark" button.
Orchestration (app.py):
Receives the uploaded file object.
Calls Preprocessor.parse_pdf(file_object) to get raw_text.
Calls BenchmarkRunner.run_full_benchmark(original_file_path="document.pdf", text_content=raw_text, memvid_params={"chunk_size_kb": 100}).
Benchmarking (BenchmarkRunner.run_full_benchmark):
Calculates original_text_size from raw_text.
Compresses raw_text with gzip and gets gzipped_text_size.
Records start_time_encode.
Calls MemVidInterface.encode_text_to_memvid(raw_text, "document_pdf_output", {"chunk_size_kb": 100}).
Inside MemVidInterface.encode_text_to_memvid:
memvid_instance = memvid.MemVid(text_data=raw_text, chunk_size_kb=100)
memvid_instance.text_to_video(video_path="data/memvid_output/document_pdf_output.mp4")
Returns ("data/memvid_output/document_pdf_output.mp4", "data/memvid_output/document_pdf_output_metadata.json").
Records end_time_encode; calculates encoding_duration.
Gets file sizes of the generated video and metadata.
Records start_time_decode.
Calls MemVidInterface.decode_memvid_to_text("data/memvid_output/document_pdf_output.mp4").
Inside MemVidInterface.decode_memvid_to_text:
memvid_instance = memvid.MemVid(video_path="data/memvid_output/document_pdf_output.mp4")
decoded_text = memvid_instance.video_to_text()
Returns decoded_text.
Records end_time_decode; calculates decoding_duration.
Compares hash of raw_text with hash of decoded_text for accuracy_check.
(Optionally performs and times chunk decoding).
Appends all collected metrics (original_text_size, video_file_size, encoding_duration, accuracy_check, etc.) to data/results/benchmarks.csv.
Returns the dictionary of metrics for this run.
Orchestration (app.py):
Receives the metrics dictionary from BenchmarkRunner.
Presentation (UI - app.py):
Displays the metrics in a formatted table or as individual stats in the Streamlit UI.
Updates any summary charts or tables if multiple runs are aggregated.
III. Visualization & Analysis Architecture (within Streamlit):
File: pages/1_📊_Results_Dashboard.py (or directly in app.py if simpler).
Logic:
Load data from data/results/benchmarks.csv using Pandas.
Perform aggregations, calculations (e.g., average speeds, storage ratios).
Use Streamlit's native charting (e.g., st.bar_chart, st.line_chart) or integrate with Matplotlib/Seaborn (by rendering plots to images displayed with st.pyplot) to visualize:
Storage size comparisons.
Encoding/Decoding speed vs. file size.
Impact of memvid parameters (if varied).
Provide filters or selectors (e.g., by document type, by file size category) to explore the data.
IV. Directory Structure (Reiteration for Clarity):
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
Use code with caution.
This architecture provides a modular and testable structure for your evaluation project, ensuring that the research and analysis goals are well-supported by the software design.