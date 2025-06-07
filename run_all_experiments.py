import os
import pandas as pd
import time

import config
import benchmark_utils # Your main benchmarking logic
# preprocessor is used by benchmark_utils, no direct import needed here unless for specific checks

# --- Configuration for Experiment Runs ---
# Define the parameters you want to iterate over
CODECS_TO_TEST = ['mp4v', 'h265', 'h264'] # Add/remove codecs as needed
DOCKER_SETTINGS_TO_TEST = [False, True]    # Test with Docker disabled and enabled

# Define which file extensions to process from the input_docs directory
SUPPORTED_FILE_EXTENSIONS = ('.txt', '.pdf', '.docx')

# --- Main Experiment Orchestration ---
def main():
    print("--- Starting Automated Benchmark Experiment Suite ---")

    all_metrics_data = [] # List to hold all individual benchmark dictionaries

    # 1. Iterate through input files
    input_files = []
    for filename in os.listdir(config.INPUT_DOCS_DIR):
        if filename.lower().endswith(SUPPORTED_FILE_EXTENSIONS):
            input_files.append(os.path.join(config.INPUT_DOCS_DIR, filename))
    
    if not input_files:
        print(f"No supported files found in {config.INPUT_DOCS_DIR}. Exiting.")
        return

    print(f"Found {len(input_files)} files to process: {input_files}")

    total_runs = len(input_files) * len(CODECS_TO_TEST) * len(DOCKER_SETTINGS_TO_TEST)
    current_run = 0

    # 2. Iterate through parameters for each file
    for file_path in input_files:
        original_filename = os.path.basename(file_path)
        for codec in CODECS_TO_TEST:
            for use_docker in DOCKER_SETTINGS_TO_TEST:
                current_run += 1
                print(f"\n>>> Processing Run {current_run}/{total_runs}: File='{original_filename}', Codec='{codec}', Docker='{use_docker}'")
                
                # For h265/h264, Docker might be more likely to be needed/work.
                # For mp4v, Docker is usually not needed. You could add logic here
                # to skip Docker=True for mp4v if it's redundant or known not to apply.
                # Example: if codec == 'mp4v' and use_docker: continue

                try:
                    # Run the benchmark for the current combination
                    # We are not passing encoder_config_override or retriever_config_override
                    # for this automated run, assuming defaults are fine for now.
                    metrics = benchmark_utils.run_benchmark_for_file(
                        original_file_path_or_buffer=file_path,
                        original_filename=original_filename,
                        encoder_codec=codec,
                        enable_docker=use_docker
                    )
                    if metrics:
                        all_metrics_data.append(metrics)
                    else:
                        print(f"WARNING: No metrics returned for {original_filename}, codec {codec}, docker {use_docker}")
                
                except Exception as e:
                    # Catch any unexpected error during a specific run_benchmark_for_file call
                    print(f"FATAL ERROR during benchmark for {original_filename}, codec {codec}, docker {use_docker}: {e}")
                    # Create a minimal error metric entry
                    error_metric = {
                        "original_filename": original_filename,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "encoder_codec": codec,
                        "encoder_docker_enabled": use_docker,
                        "error_message": f"Run failed: {type(e).__name__} - {e}"
                    }
                    all_metrics_data.append(error_metric)
                
                time.sleep(1) # Small delay between runs, optional

    # 3. Save all collected metrics to CSV
    if all_metrics_data:
        # Define a consistent filename for the automated run results
        automated_csv_filename = f"automated_benchmarks_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        automated_csv_filepath = os.path.join(config.RESULTS_DIR, automated_csv_filename)
        
        benchmark_utils.save_metrics_to_csv(all_metrics_data, csv_filepath=automated_csv_filepath)
        print(f"\n--- All automated benchmarks completed. Results saved to: {automated_csv_filepath} ---")
        
        # 4. Perform Sanity Checks on the generated CSV
        perform_sanity_checks(automated_csv_filepath)
    else:
        print("\n--- No benchmark data collected. ---")


# --- Sanity Check Function ---
def perform_sanity_checks(csv_filepath):
    print(f"\n--- Performing Sanity Checks on: {csv_filepath} ---")
    if not os.path.exists(csv_filepath):
        print(f"ERROR: Results CSV file not found at {csv_filepath}")
        return

    try:
        df = pd.read_csv(csv_filepath)
    except Exception as e:
        print(f"ERROR: Could not read CSV file {csv_filepath} with Pandas: {e}")
        return

    if df.empty:
        print("WARNING: The CSV file is empty.")
        return

    # Expected columns (based on benchmark_utils.save_metrics_to_csv fieldnames)
    expected_columns = [
        "timestamp", "original_filename", "encoder_codec", "encoder_docker_enabled",
        "original_text_size_bytes", "gzipped_text_size_bytes",
        "memvid_video_file_size_bytes", "memvid_index_file_size_bytes",
        "total_memvid_storage_bytes", "decoded_canonical_text_size_bytes",
        "encoding_time_seconds", "decoding_full_time_seconds",
        "num_memvid_chunks", "decoding_avg_chunk_time_seconds",
        "original_text_sha256", "decoded_canonical_text_sha256",
        "accuracy_check_input_vs_decoded_passed", "error_message"
    ]

    # Check 1: Are all expected columns present?
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        print(f"WARNING: Missing expected columns in CSV: {missing_columns}")
    else:
        print("Sanity Check 1 (Columns): PASSED - All expected columns are present.")

    # Check 2: Data types (basic check for some numeric and boolean columns)
    print("\nSanity Check 2 (Data Types - Partial):")
    numeric_cols_to_check = [
        'original_text_size_bytes', 'total_memvid_storage_bytes', 
        'encoding_time_seconds', 'decoding_full_time_seconds'
    ]
    type_issues = []
    for col in numeric_cols_to_check:
        if col in df.columns:
            # Check if column can be coerced to numeric, and if there are NaNs after coercion where original wasn't empty
            try:
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                if numeric_series.isnull().sum() > df[col].isnull().sum(): # More NaNs after coercion
                    type_issues.append(f"Column '{col}' has non-numeric values that were coerced to NaN.")
            except Exception as e_type:
                type_issues.append(f"Column '{col}' could not be processed as numeric: {e_type}")
    
    bool_col_to_check = 'accuracy_check_input_vs_decoded_passed'
    if bool_col_to_check in df.columns:
        # Check if it contains only boolean-like values (True, False, or NaN/None)
        # after potential string "True"/"False" conversion if pandas didn't do it.
        # A simple check:
        unique_vals = df[bool_col_to_check].dropna().unique()
        is_bool_like = all(isinstance(val, (bool, pd.NA)) or str(val).lower() in ['true', 'false'] for val in unique_vals)
        if not is_bool_like and len(unique_vals) > 0: # len > 0 to avoid false positive on all NaN column
             type_issues.append(f"Column '{bool_col_to_check}' does not appear to be consistently boolean-like. Values: {unique_vals[:5]}")


    if type_issues:
        print("WARNING: Potential data type issues found:")
        for issue in type_issues:
            print(f"  - {issue}")
    else:
        print("  Basic data type checks for selected columns: PASSED (or no issues found).")

    # Check 3: Widespread missing values (for key metrics)
    print("\nSanity Check 3 (Missing Values):")
    key_metrics_for_null_check = [
        'original_text_size_bytes', 'total_memvid_storage_bytes', 'encoding_time_seconds'
    ]
    missing_value_warnings = []
    for col in key_metrics_for_null_check:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                # Allow nulls if there's a corresponding error message for that row
                # This is a bit more complex to check perfectly without seeing the data patterns
                # For a simple check, just report if there are nulls.
                # A more advanced check: df[df[col].isnull() & df['error_message'].isnull()]
                rows_with_null_and_no_error = df[df[col].isnull() & df['error_message'].isnull()]
                if not rows_with_null_and_no_error.empty:
                    missing_value_warnings.append(f"Column '{col}' has {len(rows_with_null_and_no_error)} missing value(s) where no error was reported for the run.")
    
    if missing_value_warnings:
        print("WARNING: Missing values found in key metrics without corresponding error messages:")
        for warning in missing_value_warnings:
            print(f"  - {warning}")
    else:
        print("  No widespread unexpected missing values in key metrics (where no run error reported): PASSED.")

    # Check 4: Look at the error_message column
    print("\nSanity Check 4 (Error Messages):")
    if 'error_message' in df.columns:
        error_rows = df[df['error_message'].notna()]
        if not error_rows.empty:
            print(f"INFO: Found {len(error_rows)} rows with error messages. Review these carefully.")
            # Print a sample of error messages or specific files
            for index, row in error_rows.head(5).iterrows(): # Show first 5 errors
                print(f"  - File: {row.get('original_filename', 'N/A')}, Codec: {row.get('encoder_codec', 'N/A')}, Docker: {row.get('encoder_docker_enabled', 'N/A')}, Error: {row['error_message']}")
        else:
            print("  No error messages found in the 'error_message' column: PASSED (all runs nominally successful).")
    else:
        print("WARNING: 'error_message' column not found.")
    
    print("\n--- Sanity Checks Completed ---")
    print("Please review the generated CSV and any warnings above for a comprehensive analysis.")

if __name__ == '__main__':
    # Ensure Docker is running if DOCKER_SETTINGS_TO_TEST includes True and you test H265/H264
    # Ensure native FFmpeg is in PATH if DOCKER_SETTINGS_TO_TEST includes False for H265/H264
    main()