# memvid-evaluator/pages/1_📊_Results_Dashboard.py

import streamlit as st
import pandas as pd
import os
import altair as alt
import numpy as np

import config

st.set_page_config(
    page_title="Results Dashboard - MemVid Evaluator",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Benchmark Results Dashboard")
st.markdown("This page displays aggregated results and visualizations from benchmark runs.")

# --- Function to list available CSV files in results directory ---
def get_available_csv_files(results_dir):
    if not os.path.exists(results_dir):
        return []
    return [f for f in os.listdir(results_dir) if f.endswith('.csv')]

# --- File Selector in Sidebar ---
st.sidebar.header("📂 Select Benchmark Data")
available_files = get_available_csv_files(config.RESULTS_DIR)

selected_csv_file = None # Initialize
if not available_files:
    st.sidebar.warning("No benchmark CSV files found in the results directory.")
    st.info(f"No benchmark CSV files found in '{config.RESULTS_DIR}'. "
            "Please run benchmarks using 'App' or 'run_all_experiments.py' first.")
else:
    # Try to default to 'benchmarks.csv' if it exists, else the first available file
    default_selection_index = 0
    if config.DEFAULT_BENCHMARK_RESULTS_FILE.split(os.sep)[-1] in available_files:
        default_selection_index = available_files.index(config.DEFAULT_BENCHMARK_RESULTS_FILE.split(os.sep)[-1])
    
    selected_csv_filename = st.sidebar.selectbox(
        "Choose a benchmark CSV file to load:",
        options=available_files,
        index=default_selection_index,
        help="Select the CSV file containing benchmark results you want to visualize."
    )
    if selected_csv_filename:
        selected_csv_file = os.path.join(config.RESULTS_DIR, selected_csv_filename)
        st.sidebar.caption(f"Loading data from: `{selected_csv_filename}`")


# --- Load Data Function (now takes filepath as argument) ---
@st.cache_data(ttl=30) 
def load_benchmark_data(csv_filepath_to_load): # Takes filepath as arg
    if csv_filepath_to_load and os.path.exists(csv_filepath_to_load): # Check if path is valid
        try:
            df = pd.read_csv(csv_filepath_to_load)
            if df.empty:
                return pd.DataFrame() # Handled by later checks

            # --- Data Cleaning and Type Conversion (same as before) ---
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            numeric_cols = [
                'original_text_size_bytes', 'gzipped_text_size_bytes',
                'memvid_video_file_size_bytes', 'memvid_index_file_size_bytes', 
                'total_memvid_storage_bytes', 'decoded_canonical_text_size_bytes',
                'encoding_time_seconds', 'decoding_full_time_seconds',
                'num_memvid_chunks', 'decoding_avg_chunk_time_seconds',
                'corpus_source_files_count' # Make sure this is present or handled
            ]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            bool_cols = ['encoder_docker_enabled', 'accuracy_check_input_vs_decoded_passed']
            for col in bool_cols:
                if col in df.columns:
                    if df[col].dtype == 'object' or pd.api.types.is_string_dtype(df[col]):
                         df[col] = df[col].astype(str).str.lower().map({'true': True, 'false': False, '': pd.NA}).astype('boolean')
                    else:
                         df[col] = df[col].astype('boolean')

            # Ratio Calculation (same as before)
            df['ratio_memvid_vs_original'] = pd.NA 
            df['ratio_memvid_vs_gzipped'] = pd.NA   
            source_cols_for_ratio1 = ['total_memvid_storage_bytes', 'original_text_size_bytes']
            source_cols_for_ratio2 = ['total_memvid_storage_bytes', 'gzipped_text_size_bytes']
            if all(c in df.columns and pd.api.types.is_numeric_dtype(df[c]) for c in source_cols_for_ratio1):
                denom_orig = df['original_text_size_bytes'].replace(0, float('nan')) 
                if not denom_orig.isnull().all():
                    df['ratio_memvid_vs_original'] = (df['total_memvid_storage_bytes'] / denom_orig)
                    df['ratio_memvid_vs_original'] = pd.to_numeric(df['ratio_memvid_vs_original'], errors='coerce').replace([float('inf'), -float('inf')], float('nan'))
            if all(c in df.columns and pd.api.types.is_numeric_dtype(df[c]) for c in source_cols_for_ratio2):
                denom_gzip = df['gzipped_text_size_bytes'].replace(0, float('nan'))
                if not denom_gzip.isnull().all():
                    df['ratio_memvid_vs_gzipped'] = (df['total_memvid_storage_bytes'] / denom_gzip)
                    df['ratio_memvid_vs_gzipped'] = pd.to_numeric(df['ratio_memvid_vs_gzipped'], errors='coerce').replace([float('inf'), -float('inf')], float('nan'))
            if 'ratio_memvid_vs_original' in df.columns: df['ratio_memvid_vs_original'] = df['ratio_memvid_vs_original'].astype('Float64')
            if 'ratio_memvid_vs_gzipped' in df.columns: df['ratio_memvid_vs_gzipped'] = df['ratio_memvid_vs_gzipped'].astype('Float64')
            
            return df
        except pd.errors.EmptyDataError: # CSV exists but is empty
            st.warning(f"The selected results file '{os.path.basename(csv_filepath_to_load)}' is empty.")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error loading or processing data from {os.path.basename(csv_filepath_to_load)}: {e}")
            return pd.DataFrame()
    else: # selected_csv_file is None or path doesn't exist
        return pd.DataFrame()


# Load data based on sidebar selection
df_results = load_benchmark_data(selected_csv_file) # Pass the selected file path

# Messages based on data loading outcome
if selected_csv_file is None and available_files : # No file selected but files are available
    st.info("Select a benchmark CSV file from the sidebar to view results.")
elif not df_results.empty: # Data loaded successfully
    st.success(f"Successfully loaded data from '{os.path.basename(selected_csv_file)}'.")
    # Proceed with filters and charts (the rest of your existing dashboard logic)
    st.sidebar.markdown("---") # Separator
    st.sidebar.header("📊 Dashboard Filters")
    df_filtered = df_results.copy()

    # --- Sidebar Filters (same as before) ---
    if 'original_filename' in df_filtered.columns:
        all_filenames = ['All'] + sorted(df_filtered['original_filename'].dropna().unique().tolist())
        selected_filename_filter = st.sidebar.selectbox("Filter by Original Filename:", options=all_filenames, index=0, key="filter_filename") # Added key
        if selected_filename_filter != "All": df_filtered = df_filtered[df_filtered['original_filename'] == selected_filename_filter]

    if 'encoder_codec' in df_filtered.columns and not df_filtered['encoder_codec'].isnull().all():
        all_codecs = ['All'] + sorted(df_filtered['encoder_codec'].dropna().unique().tolist())
        selected_codec_filter = st.sidebar.selectbox("Filter by Encoder Codec:", options=all_codecs, index=0, key="filter_codec")
        if selected_codec_filter != "All": df_filtered = df_filtered[df_filtered['encoder_codec'] == selected_codec_filter]

    if 'encoder_docker_enabled' in df_filtered.columns and not df_filtered['encoder_docker_enabled'].isnull().all():
        unique_docker_options = df_filtered['encoder_docker_enabled'].dropna().unique()
        docker_options_map = {str(val): val for val in unique_docker_options}
        display_docker_options = ['All'] + sorted(docker_options_map.keys(), key=lambda x: (x != 'True', x))
        selected_docker_filter_str = st.sidebar.selectbox("Filter by Docker Enabled:", options=display_docker_options, index=0, key="filter_docker")
        if selected_docker_filter_str != "All":
            df_filtered = df_filtered[df_filtered['encoder_docker_enabled'] == docker_options_map[selected_docker_filter_str]]
    
    if 'accuracy_check_input_vs_decoded_passed' in df_filtered.columns and not df_filtered['accuracy_check_input_vs_decoded_passed'].isnull().all():
        accuracy_options_map = {"All": None, "Passed Only": True, "Failed Only": False}
        selected_accuracy_key = st.sidebar.selectbox(
            "Filter by Accuracy (Input vs Decoded):", options=list(accuracy_options_map.keys()), index=0, key="filter_accuracy"
        )
        if accuracy_options_map[selected_accuracy_key] is not None:
            df_filtered = df_filtered[df_filtered['accuracy_check_input_vs_decoded_passed'] == accuracy_options_map[selected_accuracy_key]]
    
    # ... (The rest of your dashboard: Header, Summary Statistics, Visualizations, Data Table, Download Button) ...
    # ... (This part remains identical to your last working version for charts) ...
    st.header("Overall Statistics & Visualizations")
    if df_filtered.empty and not df_results.empty: # df_results has data, but df_filtered is empty
        st.warning("No data matches the current filter criteria.")
    elif not df_filtered.empty: # df_filtered has data
        st.subheader("Summary Statistics (Filtered Data)")
        # (Summary Stats code...)
        cols_to_describe = [
            'original_text_size_bytes', 'gzipped_text_size_bytes', 
            'total_memvid_storage_bytes', 'decoded_canonical_text_size_bytes',
            'encoding_time_seconds', 'decoding_full_time_seconds',
            'num_memvid_chunks', 'ratio_memvid_vs_original', 'ratio_memvid_vs_gzipped'
        ]
        existing_cols_to_describe = [col for col in cols_to_describe if col in df_filtered.columns and pd.api.types.is_numeric_dtype(df_filtered[col])]
        if existing_cols_to_describe:
            st.write(df_filtered[existing_cols_to_describe].describe(percentiles=[.25, .5, .75, .95]).T.style.format("{:,.2f}"))
        else:
            st.info("Not enough numeric data for summary statistics with current filters.")

        st.subheader("Visualizations (Filtered Data)")
        # Chart 1: Storage Ratios (same as before)
        st.markdown("#### Storage Size Ratios (MemVid vs. Original/Gzipped)")
        # ... (Chart 1 code from previous version) ...
        ratio_cols_exist = all(col in df_filtered.columns and pd.api.types.is_numeric_dtype(df_filtered[col]) for col in ['ratio_memvid_vs_original', 'ratio_memvid_vs_gzipped'])
        if ratio_cols_exist:
            df_ratios_melted = df_filtered.melt(
                id_vars=['original_filename', 'encoder_codec'],
                value_vars=['ratio_memvid_vs_original', 'ratio_memvid_vs_gzipped'],
                var_name='Ratio Type',
                value_name='Ratio Value'
            ).dropna(subset=['Ratio Value'])
            df_ratios_melted['Ratio Type'] = df_ratios_melted['Ratio Type'].replace({
                'ratio_memvid_vs_original': 'vs. Original Text',
                'ratio_memvid_vs_gzipped': 'vs. Gzipped Text'
            })

            if not df_ratios_melted.empty:
                ratio_chart = alt.Chart(df_ratios_melted).mark_bar().encode(
                    x=alt.X('Ratio Value:Q', title='Storage Ratio Multiplier (Lower is Better)', scale=alt.Scale(zero=False)), 
                    y=alt.Y('original_filename:N', title='Original File', sort=alt.EncodingSortField(field="Ratio Value", op="mean", order='descending') if len(df_ratios_melted['original_filename'].unique()) > 1 else None),
                    color='Ratio Type:N',
                    tooltip=['original_filename', 'encoder_codec', 'Ratio Type', alt.Tooltip('Ratio Value:Q', format='.2f')]
                ).properties(title='MemVid Storage Ratio')
                st.altair_chart(ratio_chart, use_container_width=True)
            else:
                st.info("Not enough valid data to display storage ratio chart with current filters (ratios might be NaN or all filtered out).")
        else:
            st.info("Ratio columns for storage size ratios are missing, not numeric, or all NaN after filtering.")

        # Chart 2: Processing Times (same as before)
        st.markdown("#### Processing Times vs. Original Text Size")
        # ... (Chart 2 code from previous version) ...
        time_chart_cols_needed = ['original_text_size_bytes', 'encoding_time_seconds', 'decoding_full_time_seconds', 'encoder_codec']
        time_chart_numeric_cols = ['original_text_size_bytes', 'encoding_time_seconds', 'decoding_full_time_seconds']
        if all(col in df_filtered.columns for col in time_chart_cols_needed) and \
           all(pd.api.types.is_numeric_dtype(df_filtered[col]) for col in time_chart_numeric_cols):
            df_times = df_filtered[time_chart_cols_needed].copy()
            df_times.dropna(subset=time_chart_numeric_cols, inplace=True)
            for col in time_chart_numeric_cols:
                if not df_times.empty: df_times = df_times[df_times[col] > 0]
            if not df_times.empty:
                df_times_melted = df_times.melt(id_vars=['original_text_size_bytes', 'encoder_codec'], value_vars=['encoding_time_seconds', 'decoding_full_time_seconds'], var_name='Process Type', value_name='Time (seconds)')
                df_times_melted['Process Type'] = df_times_melted['Process Type'].replace({'encoding_time_seconds': 'Encoding', 'decoding_full_time_seconds': 'Full Decoding'})
                time_chart = alt.Chart(df_times_melted).mark_point(filled=True, size=70, opacity=0.7).encode(
                    x=alt.X('original_text_size_bytes:Q', title='Original Text Size (bytes)', scale=alt.Scale(type="log", zero=False)),
                    y=alt.Y('Time (seconds):Q', title='Time (seconds)', scale=alt.Scale(type="log", zero=False)),
                    color='Process Type:N', shape='encoder_codec:N',
                    tooltip=['original_text_size_bytes', 'encoder_codec', 'Process Type', alt.Tooltip('Time (seconds):Q', format='.4f')]
                ).properties(title='Processing Time vs. Original Text Size (Log-Log Scale)').interactive()
                st.altair_chart(time_chart, use_container_width=True)
            else: st.info("Not enough valid (positive, non-NaN) data to display processing time chart.")
        else: st.info("Required columns for processing time chart are missing or not numeric.")

        # Chart 3: Actual Storage Sizes (with linear scale, same as before)
        st.markdown("#### Comparison of Actual Storage Sizes")
        # ... (Chart 3 code from previous version with linear scale) ...
        size_chart_cols_needed = ['original_filename', 'original_text_size_bytes', 'gzipped_text_size_bytes', 'total_memvid_storage_bytes', 'encoder_codec']
        size_chart_numeric_cols = ['original_text_size_bytes', 'gzipped_text_size_bytes', 'total_memvid_storage_bytes']
        if all(col in df_filtered.columns for col in size_chart_cols_needed) and \
           all(pd.api.types.is_numeric_dtype(df_filtered[col]) for col in size_chart_numeric_cols):
            df_sizes = df_filtered[size_chart_cols_needed].copy()
            df_sizes.dropna(subset=size_chart_numeric_cols, inplace=True)
            df_sizes_for_plot = df_sizes.copy() 
            if not df_sizes_for_plot.empty:
                df_sizes_melted = df_sizes_for_plot.melt(id_vars=['original_filename', 'encoder_codec'], value_vars=['original_text_size_bytes', 'gzipped_text_size_bytes', 'total_memvid_storage_bytes'], var_name='Storage Type', value_name='Size (bytes)')
                if not df_sizes_melted.empty and not df_sizes_melted['Size (bytes)'].isnull().all():
                    df_sizes_melted['Storage Type'] = df_sizes_melted['Storage Type'].replace({'original_text_size_bytes': 'Original Text', 'gzipped_text_size_bytes': 'Gzipped Text', 'total_memvid_storage_bytes': 'MemVid Total'})
                    size_chart = alt.Chart(df_sizes_melted).mark_bar().encode(
                        x=alt.X('original_filename:N', title='Original File', sort=alt.EncodingSortField(field="Size (bytes)", op="sum", order='descending') if len(df_sizes_melted['original_filename'].unique()) > 1 else None),
                        y=alt.Y('Size (bytes):Q', title='Size (bytes)', scale=alt.Scale(zero=True)), 
                        color='Storage Type:N',
                        column=alt.Column('encoder_codec:N', title="Codec") if len(df_sizes_melted['encoder_codec'].unique()) > 1 and len(df_sizes_melted['encoder_codec'].unique()) < 6 else alt.Undefined,
                        tooltip=['original_filename', 'encoder_codec', 'Storage Type', alt.Tooltip('Size (bytes):Q', format=',.0f')]
                    ).properties(title='Comparison of Actual Storage Sizes (Linear Scale)')
                    st.altair_chart(size_chart, use_container_width=True)
                else: st.info("Not enough valid data for actual storage size chart after melting.")
            else: st.info("Not enough valid (non-NaN) data for actual storage size chart.")
        else: st.info("Required columns for actual storage size chart are missing or not numeric.")


        st.subheader("Filtered Benchmark Data Table")
        st.dataframe(df_filtered)
        csv_export = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv_export,
            file_name='filtered_benchmark_results.csv',
            mime='text/csv',
        )
# elif not os.path.exists(config.DEFAULT_BENCHMARK_RESULTS_FILE) and df_results.empty: # Already handled at top
#     pass