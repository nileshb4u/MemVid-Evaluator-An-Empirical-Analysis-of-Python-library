# memvid-evaluator/app.py

import streamlit as st
import os
import pandas as pd # Keep for potential future use, though dashboard handles most pd work

import config
import benchmark_utils # This now uses the updated interface

# --- Page Configuration ---
st.set_page_config(
    page_title="MemVid Evaluator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Helper Functions for UI ---
def display_metrics(metrics_dict):
    """Displays benchmark metrics in a structured way."""
    if not metrics_dict:
        st.warning("No metrics to display.")
        return

    st.subheader(f"Benchmark Results for: {metrics_dict.get('original_filename', 'N/A')}")

    if metrics_dict.get("error_message"):
        # Display multiline error messages better
        error_lines = metrics_dict['error_message'].split('. ')
        for line in error_lines:
            if line.strip():
                st.error(line.strip() + ".")


    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Timestamp", value=metrics_dict.get("timestamp", "N/A"))
        st.metric(label="Encoder Codec", value=str(metrics_dict.get("encoder_codec", "N/A")))
        st.metric(label="Encoder Docker Used", value=str(metrics_dict.get("encoder_docker_enabled", "N/A")))

    with col2:
        st.subheader("Storage Metrics")
        st.metric(label="Original Text Size", value=f"{metrics_dict.get('original_text_size_bytes', 0):,} bytes")
        st.metric(label="Gzipped Text Size", value=f"{metrics_dict.get('gzipped_text_size_bytes', 0):,} bytes")
        st.metric(label="Decoded Canonical Text Size", value=f"{metrics_dict.get('decoded_canonical_text_size_bytes', 0):,} bytes")

    with col3:
        st.subheader("MemVid Storage")
        st.metric(label="MemVid Video File Size", value=f"{metrics_dict.get('memvid_video_file_size_bytes', 0):,} bytes")
        st.metric(label="MemVid Index File Size", value=f"{metrics_dict.get('memvid_index_file_size_bytes', 0):,} bytes") # Updated name
        st.metric(label="Total MemVid Storage", value=f"{metrics_dict.get('total_memvid_storage_bytes', 0):,} bytes")


    st.markdown("---")
    col_perf, col_acc, col_chunk = st.columns(3)

    with col_perf:
        st.subheader("Performance")
        st.metric(label="Encoding Time", value=f"{metrics_dict.get('encoding_time_seconds', 0):.4f} s")
        st.metric(label="Full Decoding Time", value=f"{metrics_dict.get('decoding_full_time_seconds', 0):.4f} s")
        avg_chunk_time = metrics_dict.get("decoding_avg_chunk_time_seconds")
        if avg_chunk_time is not None:
            st.metric(label="Avg. Sampled Chunk Decode Time", value=f"{avg_chunk_time:.6f} s")
        else:
            st.metric(label="Avg. Sampled Chunk Decode Time", value="N/A")


    with col_acc:
        st.subheader("Accuracy")
        accuracy_passed = metrics_dict.get("accuracy_check_input_vs_decoded_passed", False) # Updated name
        accuracy_status = "✅ PASSED" if accuracy_passed else "❌ FAILED"
        st.metric(label="Input vs. Decoded Canonical", value=accuracy_status)
        st.caption("Compares original input text SHA256 vs. SHA256 of text decoded from MemVid.")
        if not accuracy_passed:
            st.info("NOTE: A 'FAILED' check here indicates MemVid's encoding process (e.g., internal chunking with overlap) transformed the original input text.")
        st.markdown(f"**Original Text SHA256:**")
        st.code(metrics_dict.get('original_text_sha256', 'N/A'), language=None)
        st.markdown(f"**Decoded Canonical Text SHA256:**")
        st.code(metrics_dict.get('decoded_canonical_text_sha256', 'N/A'), language=None)


    with col_chunk:
        st.subheader("Chunking Info")
        st.metric(label="Number of MemVid Chunks", value=str(metrics_dict.get("num_memvid_chunks", "N/A")))
        # Display build_stats if available (from memvid_interface) - this might be too much here
        # We can get encoder chunking details from index preview in metadata function if needed
        # encoder_chunk_cfg = metrics_dict.get("encoder_config_params", {}).get("chunking", "N/A")
        # st.metric(label="Encoder Internal Chunking Cfg", value=str(encoder_chunk_cfg))


    st.markdown("---")
    with st.expander("Show Raw Metrics Data"):
        st.json(metrics_dict)

    # Provide download links for generated files
    output_basename = os.path.splitext(metrics_dict.get("original_filename", "output"))[0]
    
    # Video file
    video_file_name = f"{output_basename}.mp4" # Assuming mp4 for simplicity, codec might change this
    video_file_path_expected = os.path.join(config.MEMVID_OUTPUT_DIR, video_file_name)
    if os.path.exists(video_file_path_expected):
        with open(video_file_path_expected, "rb") as fp:
            st.download_button(
                label=f"⬇️ Download MemVid Video ({video_file_name})",
                data=fp,
                file_name=video_file_name, # Keep original name for download
                mime="video/mp4"
            )
            
    # Index file
    index_file_name = f"{output_basename}_index.json"
    index_file_path_expected = os.path.join(config.MEMVID_OUTPUT_DIR, index_file_name)
    if os.path.exists(index_file_path_expected):
        with open(index_file_path_expected, "rb") as fp:
            st.download_button(
                label=f"⬇️ Download MemVid Index ({index_file_name})",
                data=fp,
                file_name=index_file_name,
                mime="application/json"
            )


# --- Main Application UI ---
st.title("🔬 MemVid Library Evaluator")
st.markdown("""
This application benchmarks the `memvid` library for its performance in encoding text data into video format and vice-versa.
Upload a document, configure encoding parameters, and view detailed metrics.
""")

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    uploaded_file = st.file_uploader(
        "Upload a document (TXT, PDF, DOCX)",
        type=["txt", "pdf", "docx"]
    )

    st.subheader("MemVid Encoder Settings")
    # Options for codec. Add more if MemVid supports them well.
    # 'h265' and 'h264' often require FFmpeg (native or Docker). 'mp4v' is OpenCV native.
    selected_codec = st.selectbox(
        "Encoder Codec:",
        options=['mp4v', 'h265', 'h264', 'avc1', 'xvid'], # Common codecs
        index=0, # Default to mp4v
        help="Video codec for MemVid encoding. Some codecs (h265/h264) may require FFmpeg or Docker."
    )

    encoder_use_docker = st.checkbox(
        "Use Docker for Encoder",
        value=False, # Default to False for simpler local testing
        help="Enable if MemVid should use its Docker-based FFmpeg backend for encoding (if supported for the codec)."
    )
    
    # Placeholder for future advanced encoder config (e.g., QR code params, internal chunking)
    # with st.expander("Advanced Encoder Config (JSON)"):
    #     encoder_adv_config_str = st.text_area("Encoder JSON Config:", value="{}", height=100,
    #                                      help="JSON string for advanced MemvidEncoder config options.")


    run_button = st.button("🚀 Run Benchmark", type="primary", disabled=(uploaded_file is None))

# --- Main Area for Results ---
if 'last_benchmark_metrics' not in st.session_state:
    st.session_state.last_benchmark_metrics = None

if run_button and uploaded_file is not None:
    # Parse advanced config if implemented
    # adv_encoder_cfg = None
    # try:
    #     if encoder_adv_config_str and encoder_adv_config_str.strip() != "{}":
    #         adv_encoder_cfg = json.loads(encoder_adv_config_str)
    # except json.JSONDecodeError:
    #     st.error("Invalid JSON in Advanced Encoder Config. Using default.")
    #     adv_encoder_cfg = None

    with st.spinner(f"Processing {uploaded_file.name} with codec '{selected_codec}' (Docker: {encoder_use_docker})..."):
        try:
            metrics = benchmark_utils.run_benchmark_for_file(
                original_file_path_or_buffer=uploaded_file,
                original_filename=uploaded_file.name,
                # Pass new parameters:
                encoder_codec=selected_codec,
                enable_docker=encoder_use_docker,
                encoder_config_override=None, # Pass adv_encoder_cfg here if using
                retriever_config_override=None # Not configurable via UI yet
            )

            if metrics:
                benchmark_utils.save_metrics_to_csv([metrics])
                st.session_state.last_benchmark_metrics = metrics
            else:
                st.error("Benchmarking did not return any metrics.")
                st.session_state.last_benchmark_metrics = {"error_message": "Benchmarking returned no data."}

        except Exception as e:
            st.error(f"An unexpected error occurred during benchmarking: {e}")
            st.exception(e)
            st.session_state.last_benchmark_metrics = {"error_message": f"Unexpected error: {e}"}

# Display results
if st.session_state.last_benchmark_metrics:
    display_metrics(st.session_state.last_benchmark_metrics)
else:
    st.info("Upload a file and configure settings, then click 'Run Benchmark' to see results.")

st.markdown("---")
st.caption(f"Output files (videos, indexes) are stored in: `{os.path.abspath(config.MEMVID_OUTPUT_DIR)}`")
st.caption(f"Benchmark CSV results are stored in: `{os.path.abspath(config.DEFAULT_BENCHMARK_RESULTS_FILE)}`")

# Cleanup options
with st.sidebar.expander("⚠️ Advanced: Clear Output Data"):
    st.warning("This will delete generated MemVid files and benchmark results.")
    if st.button("🗑️ Clear MemVid Output Directory"):
        try:
            cleared_count = 0
            if os.path.exists(config.MEMVID_OUTPUT_DIR):
                for f_name in os.listdir(config.MEMVID_OUTPUT_DIR):
                    if f_name.endswith((".mp4", ".json")): # Be more specific
                        os.remove(os.path.join(config.MEMVID_OUTPUT_DIR, f_name))
                        cleared_count +=1
            st.success(f"Cleared {cleared_count} files from {config.MEMVID_OUTPUT_DIR}")
            if st.session_state.last_benchmark_metrics:
                st.session_state.last_benchmark_metrics = None # Clear displayed metrics
                st.rerun() # Rerun to update the page display
        except Exception as e:
            st.error(f"Failed to clear MemVid output directory: {e}")

    if st.button("🗑️ Clear Benchmark Results CSV"):
        results_file = config.DEFAULT_BENCHMARK_RESULTS_FILE
        if os.path.exists(results_file):
            try:
                os.remove(results_file)
                st.success(f"Cleared {results_file}")
            except Exception as e:
                st.error(f"Failed to clear benchmark results CSV: {e}")
        else:
            st.info("Benchmark results CSV does not exist.")