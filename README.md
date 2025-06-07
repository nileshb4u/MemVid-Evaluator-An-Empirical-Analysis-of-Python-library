# MemVid-Evaluator-An-Empirical-Analysis-of-Python-library


This project provides a framework and tools to empirically evaluate the **MemVid** library (version 0.2.x), particularly its core functionalities for encoding textual data into a video format (reportedly using QR codes) and subsequently retrieving that text.

## 📌 Evaluation Focus

- **Storage Efficiency**: Comparing MemVid's storage footprint against original and compressed text.
- **Processing Speed**: Measuring encoding and decoding times.
- **Data Transformation & Fidelity**: Understanding how MemVid processes input text and the accuracy of retrieval.

The MemVid library itself (v0.2.x) is a comprehensive AI memory system, but this evaluator primarily focuses on foundational text-to-video encoding and retrieval aspects (`MemvidEncoder` and `MemvidRetriever`).

## 🚀 Features of This Evaluator

- **Automated Benchmarking**: `run_all_experiments.py` tests multiple files and parameter configurations.
- **Interactive Application**: Streamlit-based app for file upload, parameter selection, benchmarking, and result viewing.
- **Results Dashboard**: Visualize and filter benchmark results from `benchmarks.csv` via Streamlit.
- **Modular Codebase**:
  - `preprocessor.py`: Text extraction.
  - `memvid_interface.py`: MemVid wrapper.
  - `benchmark_utils.py`: Core benchmarking logic.
- **Data-Driven Analysis**: All metrics saved to `benchmarks.csv`.

## ❓ Key Research Questions

- How does MemVid’s storage compare to raw and gzipped text?
- What are encoding and decoding speeds across different sizes/codecs?
- Does retrieved text match the input exactly?
- How do codecs or Docker settings influence performance?

## 🛠️ Setup and Installation

### Prerequisites

- Python 3.9+
- `pip`, `git`
- `libmagic1` (for `python-magic-bin`): 
  - Windows: usually pre-included
  - Linux: `sudo apt-get install libmagic1`
  - macOS: `brew install libmagic`
- Optional for h265/h264 codecs:
  - FFmpeg in system PATH or
  - Docker (recommended)

### Installation

```bash
git clone https://github.com/your-username/memvid-evaluator.git
cd memvid-evaluator
python -m venv venv
# Activate:
# macOS/Linux: source venv/bin/activate
# Windows (CMD): venv\Scripts\activate.bat
# Windows (PowerShell): venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 🚀 Usage

### 1. Automated Batch Testing

Edit `run_all_experiments.py` to select:
- `CODECS_TO_TEST` (e.g., `['mp4v', 'h265']`)
- `DOCKER_SETTINGS_TO_TEST` (e.g., `[False, True]`)

Run:
```bash
python run_all_experiments.py
```

Outputs:
- Progress printed to console.
- CSV saved to `data/results/`.
- Files saved to `data/memvid_output/`.

### 2. Interactive Streamlit App

```bash
streamlit run app.py
```

- Upload file, select codec and Docker, run benchmark.
- Results saved to `benchmarks.csv` and displayed on UI.
- View dashboard from `📊 Results Dashboard` page.

## 📁 Project Structure

```
memvid-evaluator/
├── app.py
├── run_all_experiments.py
├── requirements.txt
├── preprocessor.py
├── memvid_interface.py
├── benchmark_utils.py
├── config.py
├── pages/
│   └── 1_📊_Results_Dashboard.py
├── data/
│   ├── input_docs/
│   ├── results/
│   └── memvid_output/
```

## 📜 Benchmark Output (benchmarks.csv)

- `original_text_size_bytes`, `gzipped_text_size_bytes`, `total_memvid_storage_bytes`
- `decoded_canonical_text_size_bytes`
- `encoding_time_seconds`, `decoding_full_time_seconds`
- `accuracy_check_input_vs_decoded_passed` (SHA256 match)
- `error_message` (if any)

## ⚠️ Limitations

- Only evaluates `add_text()` and `Retriever` (not RAG/LLM).
- Accuracy impacted by MemVid's internal text processing.
- Hardware-dependent results.
- PDF/DOCX text extraction may vary.

## 🤝 Contributing

Contributions and bug reports are welcome! Fork and submit PRs or open issues.

## 📄 License

This project is licensed under the **MIT License**. See `LICENSE` file.

## 🙏 Acknowledgments

Thanks to [Olow304/memvid](https://github.com/Olow304/memvid) and PyPI.org for hosting the MemVid library.
Built using Python, Streamlit, Pandas, Altair, and other open-source tools.
