# memvid-evaluator/benchmark_utils.py

import os
import time
import gzip
import hashlib
import csv
from io import BytesIO

import config
import preprocessor
import memvid_interface # This now uses the new MemvidEncoder/Retriever API

# --- Helper Functions --- (These remain the same)

def get_file_size(file_path):
    """Returns the size of a file in bytes."""
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0

def get_text_size_bytes(text_content: str):
    """Returns the size of a string in bytes (UTF-8 encoded)."""
    if text_content:
        return len(text_content.encode('utf-8'))
    return 0

def gzip_text(text_content: str):
    """Compresses text using gzip and returns the compressed size in bytes."""
    if not text_content:
        return 0
    compressed_bytes = gzip.compress(text_content.encode('utf-8'))
    return len(compressed_bytes)

def calculate_sha256(text_content: str):
    """Calculates the SHA256 hash of a string."""
    if text_content is None: # Check for None explicitly
        return ""
    return hashlib.sha256(text_content.encode('utf-8')).hexdigest()


# --- Main Benchmarking Function ---

def run_benchmark_for_file(original_file_path_or_buffer, original_filename: str,
                           # memvid_chunk_size_kb is no longer directly used by MemvidEncoder's add_text in the same way
                           # The encoder_config or codec might be more relevant now.
                           # For simplicity, let's remove memvid_chunk_size_kb from direct params for now,
                           # and assume memvid_interface will use defaults or passed-in encoder_config.
                           encoder_config_override: dict = None, # For MemvidEncoder config
                           retriever_config_override: dict = None, # For MemvidRetriever config
                           encoder_codec: str = 'mp4v', # Default to a simple codec
                           enable_docker: bool = False # Default to no Docker for simplicity
                           ):
    """
    Runs a full benchmark suite for a single input file using the new Memvid API.
    """
    metrics = {
        "original_filename": original_filename,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "encoder_codec": encoder_codec,
        "encoder_docker_enabled": enable_docker,
        # "memvid_chunk_size_kb" - This was for the old API.
        # The new MemvidEncoder.add_text has its own internal chunk_size, overlap defaults.
        # We could expose those via encoder_config_override if we want to vary them.
        "original_text_size_bytes": 0,
        "gzipped_text_size_bytes": 0,
        "memvid_video_file_size_bytes": 0,
        "memvid_index_file_size_bytes": 0, # Changed from metadata_file_size
        "total_memvid_storage_bytes": 0,
        "decoded_canonical_text_size_bytes": 0, # Size of text as stored/retrieved by memvid
        "encoding_time_seconds": 0,
        "decoding_full_time_seconds": 0,
        "decoding_avg_chunk_time_seconds": None,
        "num_memvid_chunks": "Unknown", # Default to unknown
        "original_text_sha256": "",
        "decoded_canonical_text_sha256": "", # Changed from decoded_text_sha256
        "accuracy_check_input_vs_decoded_passed": False, # Strict check
        "error_message": None
    }

    video_file_path = None
    index_file_path = None # Changed from metadata_file_path

    try:
        print(f"\n--- Benchmarking: {original_filename} (Codec: {encoder_codec}, Docker: {enable_docker}) ---")
        print("Step 1: Extracting text...")
        raw_text_input = preprocessor.extract_text_from_file(original_file_path_or_buffer)
        if raw_text_input is None:
            metrics["error_message"] = "Failed to extract text from original file."
            print(f"ERROR: {metrics['error_message']}")
            return metrics
        
        raw_text_input_stripped = raw_text_input.strip()
        if not raw_text_input_stripped:
            metrics["error_message"] = "Extracted text is empty or whitespace only."
            print(f"INFO: {metrics['error_message']}")
            return metrics

        metrics["original_text_size_bytes"] = get_text_size_bytes(raw_text_input_stripped)
        metrics["gzipped_text_size_bytes"] = gzip_text(raw_text_input_stripped)
        metrics["original_text_sha256"] = calculate_sha256(raw_text_input_stripped)
        print(f"  Original stripped text size: {metrics['original_text_size_bytes']} bytes")
        print(f"  Gzipped stripped text size: {metrics['gzipped_text_size_bytes']} bytes")

        print("Step 2: Encoding with MemVid...")
        base_output_filename = os.path.splitext(os.path.basename(original_filename))[0]
        
        start_time = time.perf_counter()
        # encode_text_to_memvid now returns (video_path, index_file_path)
        video_file_path, index_file_path = memvid_interface.encode_text_to_memvid(
            raw_text_input, # Pass the raw (non-stripped) text as input to encoder
            base_output_filename,
            encoder_config=encoder_config_override,
            enable_docker_encoder=enable_docker,
            codec=encoder_codec
        )
        metrics["encoding_time_seconds"] = time.perf_counter() - start_time
        print(f"  Encoding time: {metrics['encoding_time_seconds']:.4f} seconds")

        metrics["memvid_video_file_size_bytes"] = get_file_size(video_file_path)
        metrics["memvid_index_file_size_bytes"] = get_file_size(index_file_path) # Now index file
        metrics["total_memvid_storage_bytes"] = metrics["memvid_video_file_size_bytes"] + \
                                                metrics["memvid_index_file_size_bytes"]
        print(f"  MemVid video size: {metrics['memvid_video_file_size_bytes']} bytes")
        print(f"  MemVid index size: {metrics['memvid_index_file_size_bytes']} bytes") # Changed label
        print(f"  Total MemVid storage: {metrics['total_memvid_storage_bytes']} bytes")

        # 3. MemVid Full Decoding (Retrieving the canonical text)
        print("Step 3: Full decoding with MemVid...")
        start_time = time.perf_counter()
        # decode_memvid_to_text now requires index_file_path
        decoded_canonical_text = memvid_interface.decode_memvid_to_text(
            video_file_path,
            index_file_path,
            retriever_config=retriever_config_override
        )
        metrics["decoding_full_time_seconds"] = time.perf_counter() - start_time
        
        if decoded_canonical_text is None: # Should not happen if interface works, but check
            metrics["error_message"] = (metrics.get("error_message") or "") + \
                                   " Decoding returned None. "
            print(f"  ERROR: Full decoding returned None.")
            # Skip further processing that depends on decoded_canonical_text
            return metrics # Or handle more gracefully

        decoded_canonical_text_stripped = decoded_canonical_text.strip()
        metrics["decoded_canonical_text_sha256"] = calculate_sha256(decoded_canonical_text_stripped)
        metrics["decoded_canonical_text_size_bytes"] = get_text_size_bytes(decoded_canonical_text_stripped)
        print(f"  Full decoding time: {metrics['decoding_full_time_seconds']:.4f} seconds")
        print(f"  Decoded canonical text size: {metrics['decoded_canonical_text_size_bytes']} bytes")


        # 4. Accuracy Check: Input vs. Decoded Canonical Text
        print("Step 4: Verifying accuracy (Input vs. Decoded Canonical)...")
        if metrics["original_text_sha256"] == metrics["decoded_canonical_text_sha256"]:
            metrics["accuracy_check_input_vs_decoded_passed"] = True
            print("  Accuracy check (Input vs. Decoded Canonical): PASSED")
        else:
            metrics["accuracy_check_input_vs_decoded_passed"] = False
            current_err = metrics.get("error_message") or ""
            metrics["error_message"] = current_err + \
                                       "Accuracy (Input vs. Decoded Canonical) FAILED. "
            print(f"  Accuracy check (Input vs. Decoded Canonical): FAILED.")
            print(f"    Original Input SHA256: {metrics['original_text_sha256']}")
            print(f"    Decoded Canonical SHA256: {metrics['decoded_canonical_text_sha256']}")
            print(f"    This indicates MemvidEncoder.add_text() transformed the input text content or structure.")

        # 5. MemVid Chunk Information and Avg. Chunk Decoding
        print("Step 5: Analyzing chunks...")
        # get_memvid_metadata_info now requires index_file_path
        memvid_meta = memvid_interface.get_memvid_metadata_info(
            video_file_path,
            index_file_path,
            retriever_config=retriever_config_override
        )
        
        # Ensure num_chunks is an int if found, otherwise keep as "Unknown" or specific error
        num_chunks_val = memvid_meta.get('num_chunks', "Unknown")
        if isinstance(num_chunks_val, int):
            metrics["num_memvid_chunks"] = num_chunks_val
            print(f"  Number of MemVid chunks from metadata: {metrics['num_memvid_chunks']}")

            if metrics["num_memvid_chunks"] > 0:
                chunk_indices_to_test = [0]
                if metrics["num_memvid_chunks"] > 1: # Test last chunk if more than one
                    chunk_indices_to_test.append(metrics["num_memvid_chunks"] - 1)
                if metrics["num_memvid_chunks"] > 2: # Test a middle chunk
                     chunk_indices_to_test.append(metrics["num_memvid_chunks"] // 2)
                chunk_indices_to_test = sorted(list(set(chunk_indices_to_test)))

                total_chunk_decode_time = 0
                successful_chunk_decodes = 0
                for chunk_idx in chunk_indices_to_test:
                    # get_memvid_chunk_content now needs index_file_path
                    try:
                        start_time_chunk = time.perf_counter()
                        _ = memvid_interface.get_memvid_chunk_content( # We don't need the content, just timing it
                            video_file_path,
                            index_file_path,
                            chunk_idx,
                            retriever_config=retriever_config_override
                        )
                        total_chunk_decode_time += (time.perf_counter() - start_time_chunk)
                        successful_chunk_decodes += 1
                    except Exception as e_chunk:
                        print(f"    Error decoding chunk {chunk_idx} for timing: {e_chunk}")
                
                if successful_chunk_decodes > 0:
                    metrics["decoding_avg_chunk_time_seconds"] = total_chunk_decode_time / successful_chunk_decodes
                    print(f"  Avg. sampled chunk decoding time (for {successful_chunk_decodes} chunks): {metrics['decoding_avg_chunk_time_seconds']:.6f} seconds")
        else: # num_chunks_val was not an int (e.g., "Unknown" or error string from metadata)
            metrics["num_memvid_chunks"] = str(num_chunks_val) # Store the string representation
            print(f"  Could not determine valid number of chunks from metadata: {metrics['num_memvid_chunks']}")


    # Corrected exception handling for specific type errors
    except memvid_interface.MemVidEncodingError as e_enc:
        metrics["error_message"] = (metrics.get("error_message") or "") + f" MemVidEncodingError: {e_enc}"
        print(f"ERROR during encoding: {e_enc}")
    except memvid_interface.MemVidDecodingError as e_dec:
        metrics["error_message"] = (metrics.get("error_message") or "") + f" MemVidDecodingError: {e_dec}"
        print(f"ERROR during decoding: {e_dec}")
    except Exception as e_generic: # Catch any other unexpected errors
        error_msg = f"Benchmarking failed unexpectedly for '{original_filename}': {type(e_generic).__name__} - {e_generic}"
        metrics["error_message"] = (metrics.get("error_message") or "") + f" UnexpectedError: {e_generic}"
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc() # Print full traceback for unexpected errors
    finally:
        # We will not auto-delete files here for now, to allow inspection.
        # Cleanup can be done via Streamlit UI or manually.
        pass
    
    print(f"--- Benchmark completed for: {original_filename} ---")
    return metrics

# --- Saving Results ---

def save_metrics_to_csv(metrics_list, csv_filepath=None):
    if not metrics_list:
        return

    if csv_filepath is None:
        csv_filepath = config.DEFAULT_BENCHMARK_RESULTS_FILE
    os.makedirs(os.path.dirname(csv_filepath), exist_ok=True)
    file_exists = os.path.isfile(csv_filepath)
    
    # Updated fieldnames
    fieldnames = [
        "timestamp", "original_filename", 
        "encoder_codec", "encoder_docker_enabled", # New params
        "original_text_size_bytes", "gzipped_text_size_bytes",
        "memvid_video_file_size_bytes", "memvid_index_file_size_bytes", # index instead of metadata
        "total_memvid_storage_bytes", "decoded_canonical_text_size_bytes", # Added
        "encoding_time_seconds", "decoding_full_time_seconds",
        "num_memvid_chunks", "decoding_avg_chunk_time_seconds",
        "original_text_sha256", "decoded_canonical_text_sha256", # canonical
        "accuracy_check_input_vs_decoded_passed", # Specific accuracy check
        "error_message"
    ]
    # "accuracy_check_passed" was removed as it's now more specific

    try:
        with open(csv_filepath, mode='a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore') # extrasaction='ignore' is safer
            if not file_exists:
                writer.writeheader()
            for metrics_item in metrics_list: # Iterate through list items
                writer.writerow(metrics_item)
        print(f"Benchmark results saved to/appended to {csv_filepath}")
    except IOError as e:
        print(f"Error saving benchmark results to CSV: {e}")


# --- Example Usage (for testing this module directly) ---
if __name__ == '__main__':
    print("--- Testing Benchmark Utilities (New API) ---")
    
    sample_text_content = "This is sample text for benchmarking the new MemVid API. " * 50
    sample_text_content += "\nIt includes multiple lines and diverse characters. " * 30
    sample_text_content += "The quick brown fox 0123456789 !@#$%^&*()_+=-[]{};':\",./<>?`~"

    dummy_file_buffer = BytesIO(sample_text_content.encode('utf-8'))
    dummy_file_buffer.name = "sample_in_memory_new_api.txt"

    print(f"\n--- Benchmarking in-memory file: {dummy_file_buffer.name} ---")
    # Call with new parameters (or use defaults)
    metrics_result = run_benchmark_for_file(
        dummy_file_buffer, 
        dummy_file_buffer.name,
        encoder_codec='mp4v', # Example codec
        enable_docker=False   # Example setting
    )
    
    print("\nBenchmark Metrics:")
    if metrics_result: # Check if metrics_result is not None
        for key, value in metrics_result.items():
            print(f"  {key}: {value}")
        save_metrics_to_csv([metrics_result]) # Pass as a list
    else:
        print("  No metrics returned from benchmark run.")


    # Test with a physical file if available
    # (Ensure preprocessor.py created sample.txt or place one manually for this to run)
    # test_file_dir = os.path.join(config.BASE_DIR, 'data', 'input_docs')
    # physical_txt_file = os.path.join(test_file_dir, "sample.txt") # Make sure this file exists
    # if os.path.exists(physical_txt_file):
    #     print(f"\n--- Benchmarking physical file: {physical_txt_file} ---")
    #     metrics_result_physical = run_benchmark_for_file(
    #         physical_txt_file, 
    #         os.path.basename(physical_txt_file),
    #         encoder_codec='h265', # Example different codec
    #         enable_docker=False   # Try h265 without docker (might need native ffmpeg)
    #     )
    #     if metrics_result_physical:
    #         print("\nBenchmark Metrics (Physical File):")
    #         for key, value in metrics_result_physical.items():
    #             print(f"  {key}: {value}")
    #         save_metrics_to_csv([metrics_result_physical])
    # else:
    #     print(f"\nSkipping physical file test: '{physical_txt_file}' not found.")

    print("\n--- Benchmark Utilities Test Completed (New API) ---")