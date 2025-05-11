import requests
import argparse
import os
import base64
import io # For handling bytes as files for Pillow

try:
    import cv2 # OpenCV for video processing
except ImportError:
    print("CRITICAL ERROR: The opencv-python library is not installed. Please install it using 'pip install opencv-python'")
    cv2 = None

try:
    from PIL import Image # Pillow for image compression
except ImportError:
    print("CRITICAL ERROR: The Pillow library is not installed. Please install it using 'pip install Pillow'")
    Image = None 

# --- Configuration ---
IMGBB_API_URL = "https://api.imgbb.com/1/upload"
# IMPORTANT: Replace "YOUR_API_KEY_HERE" with your actual ImgBB API key
IMGBB_API_KEY_HARDCODED = "YOUR_API_KEY_HERE"
REQUEST_TIMEOUT = 60  # seconds
PNG_COMPRESSION_LEVEL = 9 # Pillow PNG compression level (0-9, 9 is highest)


def upload_to_imgbb(api_key, image_bytes, frame_number):
    """Uploads a single image (PNG bytes) to ImgBB."""
    if api_key == "YOUR_API_KEY_HERE" or not api_key:
        print("CRITICAL ERROR: ImgBB API Key is not set. Please edit the script and set IMGBB_API_KEY_HARDCODED.")
        return None
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        payload = {
            "key": api_key,
            "image": base64_image,
            "name": f"frame_{frame_number}.png"
        }
        print(f"Uploading frame {frame_number} (PNG) to ImgBB...")
        response = requests.post(IMGBB_API_URL, data=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        result = response.json()

        if result.get("success") and result.get("data") and result["data"].get("url"):
            image_url = result["data"]["url"]
            print(f"Frame {frame_number} uploaded successfully: {image_url}")
            return image_url
        else:
            error_message = result.get("error", {}).get("message", "Unknown error from ImgBB API.")
            print(f"Error: ImgBB API did not return a valid URL for frame {frame_number}. Message: {error_message}")
            print(f"Full ImgBB response: {result}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error uploading frame {frame_number} to ImgBB: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during upload of frame {frame_number}: {e}")
        return None

def compress_png_with_pillow(image_bytes, frame_no):
    """Compresses PNG image bytes using Pillow."""
    if Image is None: # Pillow not imported
        print(f"Pillow library not available. Skipping PNG compression for frame {frame_no}.")
        return image_bytes

    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Ensure image is in a mode that supports PNG features like transparency well
        if img.mode not in ['RGB', 'RGBA', 'L', 'LA']:
            img = img.convert("RGBA")

        optimized_buffer = io.BytesIO()
        img.save(optimized_buffer, format="PNG", optimize=True, compress_level=PNG_COMPRESSION_LEVEL)
        compressed_bytes = optimized_buffer.getvalue()
        
        original_size = len(image_bytes)
        compressed_size = len(compressed_bytes)
        if original_size > 0:
            reduction_percent = ((original_size - compressed_size) / original_size * 100)
            print(f"Frame {frame_no} PNG compression: Original: {original_size} B, Compressed: {compressed_size} B. Reduction: {reduction_percent:.2f}%")
        else:
            print(f"Frame {frame_no} PNG compression: Original: 0 B, Compressed: {compressed_size} B.")
        return compressed_bytes
    except Exception as e:
        print(f"Error during PNG compression with Pillow for frame {frame_no}: {e}. Uploading original.")
        return image_bytes

def extract_and_upload_frames(video_filepath, frame_numbers_list, api_key):
    """Extracts frames using OpenCV, compresses with Pillow, uploads to ImgBB, and prints BBCode."""
    if cv2 is None: # OpenCV not imported
        print("CRITICAL ERROR: opencv-python library is not available. Cannot proceed with frame extraction.")
        return

    if not os.path.exists(video_filepath):
        print(f"Error: Video file not found at '{video_filepath}'")
        return

    try:
        frame_numbers = sorted(list(set(f for f in frame_numbers_list if f >= 0)))
        if not frame_numbers:
             print("No valid non-negative frame numbers provided.")
             return
    except TypeError:
        print("Error: Frame numbers must be integers.")
        return
    
    cap = cv2.VideoCapture(video_filepath)
    if not cap.isOpened():
        print(f"Error: Could not open video file '{video_filepath}' using OpenCV.")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Video '{video_filepath}' opened using OpenCV. Total frames: {total_frames}.")
    print(f"Attempting to extract frames: {frame_numbers}")
    bb_codes = []

    for frame_no in frame_numbers:
        if frame_no >= total_frames:
            print(f"Skipping frame {frame_no}: Exceeds total frames ({total_frames-1} is max index) in the video.")
            continue

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = cap.read() # Read the frame

        if ret:
            print(f"Successfully read frame {frame_no} using OpenCV.")
            
            # Encode frame to PNG in memory using OpenCV
            is_success, buffer = cv2.imencode(".png", frame)
            if not is_success:
                print(f"Error: Could not encode frame {frame_no} to PNG format using OpenCV.")
                continue
            
            extracted_image_bytes = buffer.tobytes() # Get bytes from the buffer
            
            # Compress with Pillow
            final_image_bytes = compress_png_with_pillow(extracted_image_bytes, frame_no)
            
            image_url = upload_to_imgbb(api_key, final_image_bytes, frame_no)
            if image_url:
                bb_codes.append(f"[img]{image_url}[/img]")
            else:
                print(f"Failed to upload frame {frame_no}.")
        else:
            print(f"Warning: Could not read frame {frame_no} from video using OpenCV. It might be out of bounds or corrupted.")
    
    cap.release() # Release the video capture object
    print("\n--- All Specified Frames Processed ---")
    if bb_codes:
        print("\nGenerated BBCode(s):")
        for code in bb_codes:
            print(code)
    else:
        print("\nNo BBCode generated. Check errors above.")

def main():
    parser = argparse.ArgumentParser(
        description="Extracts frames using OpenCV, compresses with Pillow, uploads to ImgBB, prints BBCode.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("filepath", help="Path to the video file.")
    parser.add_argument(
        "frames", type=int, nargs='+',
        help="Space-separated list of 0-indexed frame numbers (e.g., 0 100 250)."
    )

    args = parser.parse_args()

    if IMGBB_API_KEY_HARDCODED == "YOUR_API_KEY_HERE" or not IMGBB_API_KEY_HARDCODED:
        print("CRITICAL ERROR: Set IMGBB_API_KEY_HARDCODED in the script.")
        return

    if cv2 is None: # Double check if OpenCV was imported
        print("CRITICAL ERROR: opencv-python library failed to import. Please ensure it's installed ('pip install opencv-python').")
        return
    if Image is None: # Double check if Pillow was imported
        print("CRITICAL ERROR: Pillow library failed to import. Please ensure it's installed ('pip install Pillow').")
        return
        
    extract_and_upload_frames(args.filepath, args.frames, IMGBB_API_KEY_HARDCODED)

if __name__ == "__main__":
    main()
