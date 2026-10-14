"""
Model Downloader for Kestral Surveillance Engine
Downloads official OpenCV Zoo YuNet (face detection) and SFace (face recognition) ONNX models.
"""
import os
import sys
import urllib.request

MODELS = {
    "face_detection_yunet.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "face_recognition_sface.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"
}

def download_file(url: str, dest_path: str):
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
        print(f"[OK] {os.path.basename(dest_path)} already exists ({os.path.getsize(dest_path)} bytes)")
        return

    print(f"Downloading {os.path.basename(dest_path)} from:\n  {url}")
    temp_path = dest_path + ".tmp"
    try:
        def progress(count, block_size, total_size):
            if total_size > 0:
                pct = int(count * block_size * 100 / total_size)
                sys.stdout.write(f"\r  Progress: {pct}% ({count * block_size}/{total_size} bytes)")
                sys.stdout.flush()

        urllib.request.urlretrieve(url, temp_path, reporthook=progress)
        print()
        os.rename(temp_path, dest_path)
        print(f"[SUCCESS] Saved to {dest_path} ({os.path.getsize(dest_path)} bytes)")
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        print(f"\n[ERROR] Failed to download {url}: {e}")
        raise

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    models_dir = os.path.join(backend_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    print(f"Ensuring model weights in: {models_dir}")
    for filename, url in MODELS.items():
        dest = os.path.join(models_dir, filename)
        download_file(url, dest)

    print("\nAll required model weights verified.")

if __name__ == "__main__":
    main()
