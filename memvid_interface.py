# memvid-evaluator/memvid_interface.py

import os
import json # For parsing index file
from memvid.encoder import MemvidEncoder
from memvid.retriever import MemvidRetriever # Import the retriever

import config

class MemVidEncodingError(Exception):
    """Custom exception for errors during MemVid encoding."""
    pass

class MemVidDecodingError(Exception):
    """Custom exception for errors during MemVid decoding."""
    pass

def encode_text_to_memvid(text_content: str, output_filename_base: str,
                          encoder_config: dict = None, enable_docker_encoder: bool = False,
                          codec: str = 'h265'):
    """
    Encodes text content into a MemVid video file and an associated index file.

    :param text_content: The string content to encode.
    :param output_filename_base: Base name for output (e.g., "mydoc").
                                 Video: mydoc.mp4 (or extension based on codec).
                                 Index: mydoc_index.json (or similar, TBD by lib).
    :param encoder_config: Optional config dictionary for MemvidEncoder.
    :param enable_docker_encoder: Whether to enable Docker for the encoder.
    :param codec: Video codec to use (e.g., 'h265', 'h264', 'mp4v').
    :return: Tuple (video_path, index_file_path) if successful.
    :raises MemVidEncodingError: If encoding fails.
    """
    video_filename = f"{output_filename_base}.mp4"
    video_path = os.path.join(config.MEMVID_OUTPUT_DIR, video_filename)
    index_filename = f"{output_filename_base}_index.json" # Default assumption for index filename
    index_file_path = os.path.join(config.MEMVID_OUTPUT_DIR, index_filename)

    os.makedirs(os.path.dirname(video_path), exist_ok=True) # Ensures directory exists

    print(f"Attempting to encode text with MemvidEncoder...")
    print(f"  Output video: {video_path}")
    print(f"  Output index: {index_file_path}")
    print(f"  Codec: {codec}, Docker for encoder: {enable_docker_encoder}")

    try:
        encoder_instance = MemvidEncoder(config=encoder_config, enable_docker=enable_docker_encoder)
        encoder_instance.add_text(text=text_content) # Using default internal chunking for add_text

        build_stats = encoder_instance.build_video(
            output_file=video_path,
            index_file=index_file_path,
            codec=codec,
            show_progress=False,
            auto_build_docker=enable_docker_encoder,
            allow_fallback=True
        )
        print(f"  MemvidEncoder build_video stats: {build_stats}")

        if not os.path.exists(video_path):
            raise MemVidEncodingError(f"MemvidEncoder encoding completed but video file not found: {video_path}")
        if not os.path.exists(index_file_path):
            raise MemVidEncodingError(f"MemvidEncoder encoding completed but index file not found: {index_file_path}")

        print(f"MemvidEncoder encoding successful. Video: {video_path}, Index: {index_file_path}")
        return video_path, index_file_path

    except Exception as e:
        err_msg = f"MemvidEncoder encoding failed for base '{output_filename_base}': {type(e).__name__} - {e}"
        print(f"ERROR: {err_msg}")
        raise MemVidEncodingError(err_msg) from e


def decode_memvid_to_text(video_path: str, index_file_path: str, retriever_config: dict = None):
    """
    Decodes all text content from a MemVid video file using its index.

    :param video_path: The path to the .mp4 MemVid video file.
    :param index_file_path: The path to the associated index file.
    :param retriever_config: Optional config dictionary for MemvidRetriever.
    :return: The decoded text content as a string (all concatenated chunks).
    :raises MemVidDecodingError: If decoding fails.
    """
    if not os.path.exists(video_path):
        raise MemVidDecodingError(f"Video file not found for decoding: {video_path}")
    if not os.path.exists(index_file_path):
        raise MemVidDecodingError(f"Index file not found for decoding: {index_file_path}")

    print(f"Attempting to decode all text using MemvidRetriever...")
    print(f"  Video file: {video_path}")
    print(f"  Index file: {index_file_path}")
    try:
        retriever = MemvidRetriever(video_file=video_path, index_file=index_file_path, config=retriever_config)
        
        num_chunks = None
        # Try to get num_chunks from the index file first, as it's more direct.
        try:
            with open(index_file_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            if 'metadata' in index_data and isinstance(index_data['metadata'], list):
                num_chunks = len(index_data['metadata'])
                print(f"  Determined num_chunks from index file ('metadata' list length): {num_chunks}")
        except Exception as e_idx:
            print(f"  Warning: Could not parse index file for num_chunks (via 'metadata' key): {e_idx}")

        # Fallback to retriever_stats if parsing index file failed or didn't yield num_chunks
        if num_chunks is None:
            retriever_stats = retriever.get_stats()
            if retriever_stats and isinstance(retriever_stats.get('index_summary'), dict):
                num_chunks_from_stats = retriever_stats['index_summary'].get('total_chunks')
                if num_chunks_from_stats is not None:
                    num_chunks = num_chunks_from_stats
                    print(f"  Determined num_chunks from retriever stats ('index_summary.total_chunks'): {num_chunks}")
            # Check for total_chunks directly in stats if index_summary path fails or total_chunks is not there
            if num_chunks is None and retriever_stats and isinstance(retriever_stats.get('total_chunks'), int):
                 num_chunks = retriever_stats['total_chunks']
                 print(f"  Determined num_chunks from retriever_stats.total_chunks: {num_chunks}")
        
        if num_chunks is None or not isinstance(num_chunks, int) or num_chunks < 0:
            raise MemVidDecodingError(f"Could not determine a valid number of chunks for video '{video_path}'.")

        if num_chunks == 0:
            print("  No chunks to decode, returning empty string.")
            return ""

        all_text_parts = []
        for i in range(num_chunks): # Assuming chunk_id is 0-indexed
            chunk_text = retriever.get_chunk_by_id(i)
            if chunk_text is not None:
                all_text_parts.append(chunk_text)
            else:
                print(f"  Warning: Got None for chunk_id {i}. This might indicate the chunk had no text or an issue.")
        
        decoded_text = "".join(all_text_parts)
        print(f"MemvidRetriever decoding successful. Total text length: {len(decoded_text)} chars.")
        return decoded_text

    except Exception as e:
        err_msg = f"MemvidRetriever decoding failed for video '{video_path}': {type(e).__name__} - {e}"
        print(f"ERROR: {err_msg}")
        raise MemVidDecodingError(err_msg) from e


def get_memvid_chunk_content(video_path: str, index_file_path: str, chunk_id: int, retriever_config: dict = None):
    """
    Retrieves the content of a specific chunk from a MemVid video.

    :param video_path: The path to the .mp4 MemVid video file.
    :param index_file_path: The path to the associated index file.
    :param chunk_id: The 0-based ID of the chunk to retrieve.
    :param retriever_config: Optional config dictionary for MemvidRetriever.
    :return: The text content of the specified chunk.
    :raises MemVidDecodingError: If an error occurs or chunk is not found.
    """
    if not os.path.exists(video_path):
        raise MemVidDecodingError(f"Video file not found: {video_path}")
    if not os.path.exists(index_file_path):
        raise MemVidDecodingError(f"Index file not found: {index_file_path}")
        
    try:
        retriever = MemvidRetriever(video_file=video_path, index_file=index_file_path, config=retriever_config)
        chunk_text = retriever.get_chunk_by_id(chunk_id)
        if chunk_text is None:
            print(f"Warning: No text returned for chunk_id {chunk_id} from {video_path}")
        return chunk_text
    except Exception as e:
        raise MemVidDecodingError(f"Failed to get chunk {chunk_id} for {video_path}: {type(e).__name__} - {e}") from e


def get_memvid_metadata_info(video_path: str, index_file_path: str, retriever_config: dict = None):
    """
    Retrieves metadata information, primarily the number of chunks.

    :param video_path: Path to the video file.
    :param index_file_path: Path to the index file.
    :param retriever_config: Optional config for MemvidRetriever.
    :return: A dictionary containing metadata summary.
    """
    if not os.path.exists(index_file_path):
        return {"error": f"Index file not found: {index_file_path}", "num_chunks": "Unknown"}

    metadata_summary = {"num_chunks": "Unknown"}
    try:
        # Primary way to get num_chunks: parse the index file
        with open(index_file_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        preview_chunk_metadata = []
        if 'metadata' in index_data and isinstance(index_data['metadata'], list):
            for chunk_meta in index_data['metadata'][:2]: # Preview first 2 chunks
                preview_chunk = chunk_meta.copy()
                if 'text' in preview_chunk and isinstance(preview_chunk['text'], str):
                    preview_chunk['text_length'] = len(preview_chunk['text'])
                    del preview_chunk['text']
                preview_chunk_metadata.append(preview_chunk)
        
        index_content_preview = {
            "chunk_metadata_preview": preview_chunk_metadata,
            "chunk_to_frame_preview": {k: v for i, (k,v) in enumerate(index_data.get('chunk_to_frame', {}).items()) if i < 5},
            "frame_to_chunks_preview": {k: v for i, (k,v) in enumerate(index_data.get('frame_to_chunks', {}).items()) if i < 5},
            "config_used_for_encoding_preview": index_data.get('config', {}).get('chunking') # Example: get chunking config from index
        }
        metadata_summary["index_file_content_preview"] = index_content_preview

        if 'metadata' in index_data and isinstance(index_data['metadata'], list):
            metadata_summary["num_chunks"] = len(index_data['metadata'])
        
        if os.path.exists(video_path):
            try:
                retriever = MemvidRetriever(video_file=video_path, index_file=index_file_path, config=retriever_config)
                retriever_stats = retriever.get_stats()
                metadata_summary["retriever_stats"] = retriever_stats
                # If num_chunks wasn't found from index file directly, try from stats as a fallback
                if metadata_summary["num_chunks"] == "Unknown" and \
                   retriever_stats and isinstance(retriever_stats.get('index_summary'), dict):
                    num_chunks_from_stats = retriever_stats['index_summary'].get('total_chunks')
                    if num_chunks_from_stats is not None:
                        metadata_summary["num_chunks"] = num_chunks_from_stats
                # Check for total_chunks directly in stats if index_summary path fails or total_chunks is not there
                elif metadata_summary["num_chunks"] == "Unknown" and \
                     retriever_stats and isinstance(retriever_stats.get('total_chunks'), int):
                     metadata_summary["num_chunks"] = retriever_stats['total_chunks']

            except Exception as e_retriever:
                print(f"  Warning: Could not get retriever stats: {e_retriever}")
                metadata_summary["retriever_stats_error"] = str(e_retriever)

    except Exception as e:
        metadata_summary["error"] = f"Could not fully process metadata/index: {type(e).__name__} - {e}"
    
    return metadata_summary


# --- Example Usage (for testing this module directly) ---
if __name__ == '__main__':
    print("--- Testing MemVid Interface (New API - Fully Updated) ---")
    input_sample_text = "This is a moderately long test sentence for the new MemvidEncoder and MemvidRetriever. " * 10
    input_sample_text += "We are exploring its capabilities for encoding text into video and an index file, "
    input_sample_text += "and then retrieving the text content. Hopefully, this works out well!"
    input_sample_text_stripped = input_sample_text.strip()

    base_filename = "new_api_final_test"
    test_encoder_config = None 
    test_retriever_config = None
    test_enable_docker = False 
    test_codec = 'mp4v' 
    video_fp, index_fp = None, None

    try:
        print(f"\n--- Test 1: Encoding with {test_codec} (Docker: {test_enable_docker}) ---")
        video_fp, index_fp = encode_text_to_memvid(
            input_sample_text, # Pass the original input string
            base_filename,
            encoder_config=test_encoder_config,
            enable_docker_encoder=test_enable_docker,
            codec=test_codec
        )
        print(f"Encoding successful: Video at {video_fp}, Index at {index_fp}")
        assert os.path.exists(video_fp), "Video file was not created!"
        assert os.path.exists(index_fp), "Index file was not created!"

        print("\n--- Test 2: Metadata/Index Info ---")
        metadata = get_memvid_metadata_info(video_fp, index_fp, retriever_config=test_retriever_config)
        print(f"Retrieved Metadata/Index Info (first level keys): {list(metadata.keys())}")
        if "index_file_content_preview" in metadata:
            print(f"  Index Preview (encoder chunking cfg): {metadata['index_file_content_preview'].get('config_used_for_encoding_preview')}")
        
        num_chunks_from_meta = metadata.get("num_chunks")
        print(f"  Number of chunks reported by metadata function: {num_chunks_from_meta}")
        assert "error" not in metadata, f"Error in metadata retrieval: {metadata.get('error')}"
        assert num_chunks_from_meta != "Unknown" and isinstance(num_chunks_from_meta, int) and num_chunks_from_meta >= 0, \
            f"Invalid num_chunks in metadata: {num_chunks_from_meta}"
        

        # Construct the "canonical text" from the index file for comparison
        # This is the text as it was segmented and stored by the encoder
        canonical_text_from_index = ""
        index_data_for_text = None # To store loaded index data
        if os.path.exists(index_fp):
            with open(index_fp, 'r', encoding='utf-8') as f:
                index_data_for_text = json.load(f)
            if index_data_for_text and 'metadata' in index_data_for_text and isinstance(index_data_for_text['metadata'], list):
                for chunk_info in index_data_for_text['metadata']:
                    if 'text' in chunk_info:
                        canonical_text_from_index += chunk_info['text']
        canonical_text_from_index_stripped = canonical_text_from_index.strip()


        print("\n--- Test 3: Decoding All Text ---")
        decoded_text_full = decode_memvid_to_text(video_fp, index_fp, retriever_config=test_retriever_config)
        decoded_text_full_stripped = decoded_text_full.strip()
        
        assert decoded_text_full is not None, "Decoding returned None."
        if num_chunks_from_meta > 0 : # Only assert non-empty if chunks were expected
             assert decoded_text_full_stripped != "", "Decoding returned an empty string when text was expected."
        
        print(f"Full decoding successful. Decoded text length: {len(decoded_text_full_stripped)} chars.")
        print(f"Canonical text (from index) length: {len(canonical_text_from_index_stripped)} chars.")
        
        assert decoded_text_full_stripped == canonical_text_from_index_stripped, \
            f"Decoded text does not match canonical text from index! \nCanonical (len {len(canonical_text_from_index_stripped)}): '{canonical_text_from_index_stripped[:100]}...' \nDecoded (len {len(decoded_text_full_stripped)}): '{decoded_text_full_stripped[:100]}...'"
        print("ACCURACY CHECK: Decoded text (from retriever) matches the canonical text stored in the index file.")

        if input_sample_text_stripped != canonical_text_from_index_stripped:
            print(f"NOTE: Original input text (len {len(input_sample_text_stripped)}) was transformed by MemvidEncoder's add_text() "
                  f"into the canonical text (len {len(canonical_text_from_index_stripped)}) stored in the index.")
            print(f"  Input text starts: '{input_sample_text_stripped[:50]}...'")
            print(f"  Canon text starts: '{canonical_text_from_index_stripped[:50]}...'")


        if num_chunks_from_meta > 0:
            print("\n--- Test 4: Decoding Individual Chunk (chunk_id=0) ---")
            chunk_0_text_retrieved = get_memvid_chunk_content(video_fp, index_fp, 0, retriever_config=test_retriever_config)
            assert chunk_0_text_retrieved is not None, "get_memvid_chunk_content(0) returned None"
            
            chunk_0_text_from_index = ""
            if index_data_for_text and 'metadata' in index_data_for_text and isinstance(index_data_for_text['metadata'], list) and len(index_data_for_text['metadata']) > 0:
                chunk_0_text_from_index = index_data_for_text['metadata'][0].get('text', '')

            assert chunk_0_text_retrieved.strip() == chunk_0_text_from_index.strip(), "Retrieved chunk 0 text does not match chunk 0 text from index."
            print(f"Text of chunk 0 (first 50 chars): '{chunk_0_text_retrieved[:50]}...' - Matches index content.")

        print("\n--- All MemVid Interface tests (New API - Fully Updated) completed successfully. ---")

    except (MemVidEncodingError, MemVidDecodingError) as e:
        print(f"AN ERROR OCCURRED DURING TESTING: {e}")
    except AssertionError as e:
        print(f"ASSERTION FAILED: {e}")
    except Exception as e: # Catch any other unexpected exceptions
        import traceback
        print(f"AN UNEXPECTED ERROR OCCURRED: {type(e).__name__} - {e}")
        print(traceback.format_exc())
    finally:
        if video_fp and os.path.exists(video_fp):
            os.remove(video_fp)
        if index_fp and os.path.exists(index_fp):
            os.remove(index_fp)
        print("Cleaned up test files (if any were created).")