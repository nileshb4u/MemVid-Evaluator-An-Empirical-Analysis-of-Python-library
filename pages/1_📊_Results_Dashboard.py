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
st.markdown("This page displays aggregated results and visualizations from all benchmark runs.")

# --- Load Data ---
@st.cache_data(ttl=30) 
def load_benchmark_data():
    csv_filepath = config.DEFAULT_BENCHMARK_RESULTS_FILE
    if os.path.exists(csv_filepath):
        try:
            df = pd.read_csv(csv_filepath)
            if df.empty:
                return pd.DataFrame()

            df['timestamp'] = pd.to_datetime(df['timestamp'])
            numeric_cols = [
                'original_text_size_bytes', 'gzipped_text_size_bytes',
                'memvid_video_file_size_bytes', 'memvid_index_file_size_bytes', 
                'total_memvid_storage_bytes', 'decoded_canonical_text_size_bytes',
                'encoding_time_seconds', 'decoding_full_time_seconds',
                'num_memvid_chunks', 'decoding_avg_chunk_time_seconds'
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

            df['ratio_memvid_vs_original'] = pd.NA 
            df['ratio_memvid_vs_gzipped'] = pd.NA   

            source_cols_for_ratio1 = ['total_memvid_storage_bytes', 'original_text_size_bytes']
            source_cols_for_ratio2 = ['total_memvid_storage_bytes', 'gzipped_text_size_bytes']

            if all(col in df.columns and pd.api.types.is_numeric_dtype(df[col]) for col in source_cols_for_ratio1):
                denominator_orig = df['original_text_size_bytes'].replace(0, float('nan')) 
                if not denominator_orig.isnull().all():
                    df['ratio_memvid_vs_original'] = (df['total_memvid_storage_bytes'] / denominator_orig)
                    df['ratio_memvid_vs_original'] = pd.to_numeric(df['ratio_memvid_vs_original'], errors='coerce').replace([float('inf'), -float('inf')], float('nan'))

            if all(col in df.columns and pd.api.types.is_numeric_dtype(df[col]) for col in source_cols_for_ratio2):
                denominator_gzip = df['gzipped_text_size_bytes'].replace(0, float('nan'))
                if not denominator_gzip.isnull().all():
                    df['ratio_memvid_vs_gzipped'] = (df['total_memvid_storage_bytes'] / denominator_gzip)
                    df['ratio_memvid_vs_gzipped'] = pd.to_numeric(df['ratio_memvid_vs_gzipped'], errors='coerce').replace([float('inf'), -float('inf')], float('nan'))
            
            if 'ratio_memvid_vs_original' in df.columns:
                 df['ratio_memvid_vs_original'] = df['ratio_memvid_vs_original'].astype('Float64')
            if 'ratio_memvid_vs_gzipped' in df.columns:
                 df['ratio_memvid_vs_gzipped'] = df['ratio_memvid_vs_gzipped'].astype('Float64')
            
            return df
        except pd.errors.EmptyDataError:
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error loading or processing benchmark data from {os.path.basename(csv_filepath)}: {e}")
            return pd.DataFrame()
    else:
        return pd.DataFrame()

df_results = load_benchmark_data()

if not os.path.exists(config.DEFAULT_BENCHMARK_RESULTS_FILE):
    st.info(f"Benchmark results file ('{os.path.basename(config.DEFAULT_BENCHMARK_RESULTS_FILE)}') not found. Run some benchmarks on the main 'App' page first.")
elif df_results.empty and os.path.exists(config.DEFAULT_BENCHMARK_RESULTS_FILE):
     st.warning(f"The results file '{os.path.basename(config.DEFAULT_BENCHMARK_RESULTS_FILE)}' is empty or could not be processed. Run some benchmarks.")

if not df_results.empty:
    st.sidebar.header("📊 Dashboard Filters")
    df_filtered = df_results.copy()

    # --- Sidebar Filters ---
    if 'original_filename' in df_filtered.columns:
        all_filenames = ['All'] + sorted(df_filtered['original_filename'].dropna().unique().tolist())
        selected_filename = st.sidebar.selectbox("Filter by Original Filename:", options=all_filenames, index=0)
        if selected_filename != "All": df_filtered = df_filtered[df_filtered['original_filename'] == selected_filename]

    if 'encoder_codec' in df_filtered.columns and not df_filtered['encoder_codec'].isnull().all():
        all_codecs = ['All'] + sorted(df_filtered['encoder_codec'].dropna().unique().tolist())
        selected_codec_filter = st.sidebar.selectbox("Filter by Encoder Codec:", options=all_codecs, index=0)
        if selected_codec_filter != "All": df_filtered = df_filtered[df_filtered['encoder_codec'] == selected_codec_filter]

    if 'encoder_docker_enabled' in df_filtered.columns and not df_filtered['encoder_docker_enabled'].isnull().all():
        unique_docker_options = df_filtered['encoder_docker_enabled'].dropna().unique()
        docker_options_map = {str(val): val for val in unique_docker_options}
        display_docker_options = ['All'] + sorted(docker_options_map.keys(), key=lambda x: (x != 'True', x))
        
        selected_docker_filter_str = st.sidebar.selectbox("Filter by Docker Enabled:", options=display_docker_options, index=0)
        if selected_docker_filter_str != "All":
            df_filtered = df_filtered[df_filtered['encoder_docker_enabled'] == docker_options_map[selected_docker_filter_str]]
    
    if 'accuracy_check_input_vs_decoded_passed' in df_filtered.columns and not df_filtered['accuracy_check_input_vs_decoded_passed'].isnull().all():
        accuracy_options_map = {"All": None, "Passed Only": True, "Failed Only": False}
        selected_accuracy_key = st.sidebar.selectbox(
            "Filter by Accuracy (Input vs Decoded):", options=list(accuracy_options_map.keys()), index=0
        )
        if accuracy_options_map[selected_accuracy_key] is not None:
            df_filtered = df_filtered[df_filtered['accuracy_check_input_vs_decoded_passed'] == accuracy_options_map[selected_accuracy_key]]
    
    st.header("Overall Statistics & Visualizations")
    if df_filtered.empty and not df_results.empty:
        st.warning("No data matches the current filter criteria.")
    elif not df_filtered.empty:
        st.subheader("Summary Statistics (Filtered Data)")
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

        # Chart 1: Storage Ratios
        st.markdown("#### Storage Size Ratios (MemVid vs. Original/Gzipped)")
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
                    x=alt.X('Ratio Value:Q', title='Storage Ratio Multiplier (Lower is Better)', scale=alt.Scale(zero=False)), # Ratios typically don't start at 0
                    y=alt.Y('original_filename:N', title='Original File', sort=alt.EncodingSortField(field="Ratio Value", op="mean", order='descending') if len(df_ratios_melted['original_filename'].unique()) > 1 else None),
                    color='Ratio Type:N',
                    tooltip=['original_filename', 'encoder_codec', 'Ratio Type', alt.Tooltip('Ratio Value:Q', format='.2f')]
                ).properties(title='MemVid Storage Ratio')
                st.altair_chart(ratio_chart, use_container_width=True)
            else:
                st.info("Not enough valid data to display storage ratio chart with current filters (ratios might be NaN or all filtered out).")
        else:
            st.info("Ratio columns for storage size ratios are missing, not numeric, or all NaN after filtering.")


        # Chart 2: Processing Times vs. Original File Size
        st.markdown("#### Processing Times vs. Original Text Size")
        time_chart_cols_needed = ['original_text_size_bytes', 'encoding_time_seconds', 'decoding_full_time_seconds', 'encoder_codec']
        time_chart_numeric_cols = ['original_text_size_bytes', 'encoding_time_seconds', 'decoding_full_time_seconds']
        
        if all(col in df_filtered.columns for col in time_chart_cols_needed) and \
           all(pd.api.types.is_numeric_dtype(df_filtered[col]) for col in time_chart_numeric_cols):
            
            df_times = df_filtered[time_chart_cols_needed].copy()
            df_times.dropna(subset=time_chart_numeric_cols, inplace=True)
            
            for col in time_chart_numeric_cols:
                if not df_times.empty: 
                    df_times = df_times[df_times[col] > 0]

            if not df_times.empty:
                df_times_melted = df_times.melt(
                    id_vars=['original_text_size_bytes', 'encoder_codec'],
                    value_vars=['encoding_time_seconds', 'decoding_full_time_seconds'],
                    var_name='Process Type',
                    value_name='Time (seconds)'
                )
                df_times_melted['Process Type'] = df_times_melted['Process Type'].replace({
                    'encoding_time_seconds': 'Encoding',
                    'decoding_full_time_seconds': 'Full Decoding'
                })
                time_chart = alt.Chart(df_times_melted).mark_point(filled=True, size=70, opacity=0.7).encode(
                    x=alt.X('original_text_size_bytes:Q', title='Original Text Size (bytes)', scale=alt.Scale(type="log", zero=False)),
                    y=alt.Y('Time (seconds):Q', title='Time (seconds)', scale=alt.Scale(type="log", zero=False)),
                    color='Process Type:N',
                    shape='encoder_codec:N',
                    tooltip=['original_text_size_bytes', 'encoder_codec', 'Process Type', alt.Tooltip('Time (seconds):Q', format='.4f')]
                ).properties(title='Processing Time vs. Original Text Size (Log-Log Scale)').interactive()
                st.altair_chart(time_chart, use_container_width=True)
            else:
                st.info("Not enough valid (positive, non-NaN) data to display processing time chart with current filters.")
        else:
            st.info("Required columns for processing time chart are missing or not numeric.")


        # Chart 3: Actual Storage Sizes Comparison
        st.markdown("#### Comparison of Actual Storage Sizes")
        size_chart_cols_needed = ['original_filename', 'original_text_size_bytes', 'gzipped_text_size_bytes', 'total_memvid_storage_bytes', 'encoder_codec']
        size_chart_numeric_cols = ['original_text_size_bytes', 'gzipped_text_size_bytes', 'total_memvid_storage_bytes']
        
        if all(col in df_filtered.columns for col in size_chart_cols_needed) and \
           all(pd.api.types.is_numeric_dtype(df_filtered[col]) for col in size_chart_numeric_cols):
            
            df_sizes = df_filtered[size_chart_cols_needed].copy()
            df_sizes.dropna(subset=size_chart_numeric_cols, inplace=True)
            
            # For linear scale starting at 0, we don't need to filter for col > 0,
            # unless a size of 0 is truly invalid and should not be plotted.
            # If sizes can legitimately be 0 (e.g. gzipped empty text), let them plot as 0.
            df_sizes_for_plot = df_sizes.copy() 
            # No df_sizes_positive[col] > 0 filter needed if using linear scale starting at zero

            if not df_sizes_for_plot.empty:
                df_sizes_melted = df_sizes_for_plot.melt(
                    id_vars=['original_filename', 'encoder_codec'],
                    value_vars=['original_text_size_bytes', 'gzipped_text_size_bytes', 'total_memvid_storage_bytes'],
                    var_name='Storage Type',
                    value_name='Size (bytes)'
                )

                if not df_sizes_melted.empty and not df_sizes_melted['Size (bytes)'].isnull().all():
                    df_sizes_melted['Storage Type'] = df_sizes_melted['Storage Type'].replace({
                        'original_text_size_bytes': 'Original Text',
                        'gzipped_text_size_bytes': 'Gzipped Text',
                        'total_memvid_storage_bytes': 'MemVid Total'
                    })

                    size_chart = alt.Chart(df_sizes_melted).mark_bar().encode(
                        x=alt.X('original_filename:N', title='Original File', sort=alt.EncodingSortField(field="Size (bytes)", op="sum", order='descending') if len(df_sizes_melted['original_filename'].unique()) > 1 else None),
                        # CHANGED Y-AXIS TO LINEAR SCALE, STARTING AT ZERO
                        y=alt.Y('Size (bytes):Q', title='Size (bytes)', scale=alt.Scale(zero=True)), 
                        color='Storage Type:N',
                        column=alt.Column('encoder_codec:N', title="Codec") if len(df_sizes_melted['encoder_codec'].unique()) > 1 and len(df_sizes_melted['encoder_codec'].unique()) < 6 else alt.Undefined,
                        tooltip=['original_filename', 'encoder_codec', 'Storage Type', alt.Tooltip('Size (bytes):Q', format=',.0f')]
                    ).properties(title='Comparison of Actual Storage Sizes (Linear Scale)') # Updated title
                    st.altair_chart(size_chart, use_container_width=True)
                else:
                    st.info("Not enough valid data to display actual storage size chart after melting or all values are non-positive.")
            else:
                st.info("Not enough valid (non-NaN) data to display actual storage size chart with current filters (df_sizes_for_plot became empty).")
        else:
            st.info("Required columns for actual storage size chart are missing from df_filtered or are not numeric.")

        st.subheader("Filtered Benchmark Data Table")
        st.dataframe(df_filtered)
        csv_export = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv_export,
            file_name='filtered_benchmark_results.csv',
            mime='text/csv',
        )