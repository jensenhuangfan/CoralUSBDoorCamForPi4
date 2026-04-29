import sys, time, cv2
from pathlib import Path
sys.path.append('.')
from main import CoralFaceDetector

try:
    print("--- Edge TPU Verification Test ---")
    detector = CoralFaceDetector(Path('models/ssd_mobilenet_v2_face_quant_postprocess_edgetpu.tflite'))
    
    # Grab a sample image from the known faces database
    images = list(Path('known_faces').rglob('*.jpg')) + list(Path('known_faces').rglob('*.png'))
    test_img = images[0]
    
    img = cv2.imread(str(test_img))
    print(f"Loaded test image: {test_img} (shape: {img.shape})")
    
    # Warmup Edge TPU (first run is always slightly slower as it shifts to hardware)
    detector.detect_faces(img)
    
    # Test Speed & Accuracy
    print("\nRunning inference...")
    start_time = time.time()
    results = detector.detect_faces(img)
    end_time = time.time()
    
    latency_ms = (end_time - start_time) * 1000
    
    print(f"\nRESULTS:")
    print(f"Faces Detected: {len(results)}")
    for r in results:
        print(f" - BBox (x1,y1,x2,y2): {r.bbox}, Model Confidence: {r.score * 100:.1f}%")
    print(f"Execution Latency: {latency_ms:.2f} ms")
    
    if latency_ms < 50:
        print("\nVERDICT: PASS - Inference is running at hardware-accelerated speeds! (CPU inference usually takes 100ms+)")
    else:
        print("\nVERDICT: WARNING - Latency seems high, might be dropping to CPU.")

except Exception as e:
    print(f"\nVERDICT: FAIL - {e}")

