
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import subprocess
import uuid
from werkzeug.utils import secure_filename
import threading
import json
import cv2
import numpy as np

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

processing_status = {}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def create_analysis_from_blueprint(image_path,
                                   wall_height=3.0,
                                   scale_factor=0.01,
                                   min_wall_area=500,
                                   morph_kernel_size=5):
    """
    Analyze blueprint image to extract wall contours, and detect rectangular door/window-like contours.
    Returns a JSON-serializable dict with walls (polygons in normalized coords), doors, windows, rooms (bounds).
    """
    print(f"🧾 Analyzing blueprint: {image_path}")
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError("Failed to load image for analysis.")

    h, w = img.shape[:2]
    # adaptive thresholding + invert: make walls white
    blur = cv2.GaussianBlur(img, (5,5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY_INV, 15, 5)

    # Morphology: close gaps, remove small noise
    kernel = np.ones((morph_kernel_size, morph_kernel_size), np.uint8)
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, hierarchy = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"🔎 Found {len(contours)} raw contours")

    walls = []
    doors = []
    windows = []
    all_wall_points = []

    def norm_pt(pt):
        x, y = pt
        return [float(x) / w, float(y) / h]

    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < min_wall_area:
            continue

        # Approximate polygon
        peri = cv2.arcLength(cnt, True)
        eps = max(2.0, 0.01 * peri)
        approx = cv2.approxPolyDP(cnt, eps, True)
        # convert to list of (x,y)
        pts = [tuple(p[0]) for p in approx]

        # If polygon is rectangle-like and smallish -> possible door/window
        x,y,w_rect,h_rect = cv2.boundingRect(approx)
        aspect = w_rect / float(h_rect + 1e-6)
        rect_area = w_rect * h_rect

        # Heuristics:
        # - very thin and relatively small: likely door/window symbol (on the blueprint)
        # - if 4-vertex poly and width or height small -> register as window/door
        if len(pts) == 4 and rect_area < area * 0.6 and rect_area < 5000 and (min(w_rect, h_rect) < max(w_rect,h_rect)*0.35):
            # classify by orientation/size: tall narrow -> door; short wide -> window (heuristic)
            if max(w_rect, h_rect) / float(min(w_rect, h_rect) + 1e-6) > 1.5:
                # treat as door if larger
                center = (x + w_rect/2, y + h_rect/2)
                doors.append({
                    "id": f"door_{len(doors)}",
                    "center": [center[0]/w, center[1]/h],
                    "width": w_rect / float(w),
                    "height": h_rect / float(h),
                    "area_px": rect_area
                })
                continue
            else:
                center = (x + w_rect/2, y + h_rect/2)
                windows.append({
                    "id": f"window_{len(windows)}",
                    "center": [center[0]/w, center[1]/h],
                    "width": w_rect / float(w),
                    "height": h_rect / float(h),
                    "area_px": rect_area
                })
                continue

        # otherwise treat as wall polygon
        norm_poly = [norm_pt(p) for p in pts]
        walls.append({
            "id": f"wall_{len(walls)}",
            "vertices": norm_poly,
            "thickness": 0.02  # normalized thickness; user can tune later
        })
        all_wall_points.extend(pts)

    # Create room bounds as a simple bounding box of all wall points (could be improved to segmentation)
    if len(all_wall_points) > 0:
        all_pts_arr = np.array(all_wall_points)
        min_x, min_y = np.min(all_pts_arr, axis=0)
        max_x, max_y = np.max(all_pts_arr, axis=0)
        room_bounds = {
            "id": "room_0",
            "bounds": {
                "x": float(min_x) / w,
                "y": float(min_y) / h,
                "width": float(max_x - min_x) / w,
                "height": float(max_y - min_y) / h
            },
            "center": [ (min_x+max_x)/(2*w), (min_y+max_y)/(2*h) ]
        }
        rooms = [room_bounds]
    else:
        rooms = []

    analysis = {
        "image_width": w,
        "image_height": h,
        "scale_factor": scale_factor,
        "wall_height": wall_height,
        "walls": walls,
        "doors": doors,
        "windows": windows,
        "rooms": rooms
    }

    print(f"✅ Analysis: walls={len(walls)}, doors={len(doors)}, windows={len(windows)}, rooms={len(rooms)}")
    return analysis

def process_blueprint_async(task_id, input_path, output_path):
    """Simple processing that WORKS"""
    print(f"🚀 PROCESSING: {task_id}")
    try:
        processing_status[task_id] = {"status": "processing", "progress": 10}

        # Create analysis using real blueprint analysis
        analysis_data = create_analysis_from_blueprint(input_path,
                                                      wall_height=3.0,
                                                      scale_factor=0.02,
                                                      min_wall_area=400,
                                                      morph_kernel_size=5)
        processing_status[task_id]["progress"] = 40

        # Save analysis
        analysis_file = input_path.rsplit('.', 1)[0] + '_analysis.json'
        with open(analysis_file, 'w') as f:
            json.dump(analysis_data, f, indent=2)

        print(f"💾 Saved: {analysis_file}")
        processing_status[task_id]["progress"] = 50

        # Find Blender
        blender_path = r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
        if not os.path.exists(blender_path):
            blender_path = "blender"

        processing_status[task_id]["progress"] = 60

        # Run Blender (use list command; keep shell=True on Windows if needed)
        cmd = [blender_path, "--background", "--python", "generate_model.py", "--", analysis_file, output_path]

        print(f"🎬 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, shell=True)

        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")

        if result.returncode == 0 and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            processing_status[task_id] = {
                "status": "completed",
                "progress": 100,
                "model_file": os.path.basename(output_path),
                "analysis": {
                    "walls_detected": len(analysis_data['walls']),
                    "doors_detected": len(analysis_data['doors']),
                    "windows_detected": len(analysis_data['windows']),
                    "rooms_detected": len(analysis_data['rooms']),
                    "model_size_bytes": file_size,
                    "scale_factor": analysis_data['scale_factor']
                }
            }
            print(f"✅ SUCCESS: {output_path} created ({file_size} bytes)")
        else:
            error_msg = f"Failed: {result.stderr or 'Unknown error'}"
            processing_status[task_id] = {"status": "error", "progress": 0, "error": error_msg}

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"❌ {error_msg}")
        processing_status[task_id] = {"status": "error", "progress": 0, "error": error_msg}

@app.route("/api/upload", methods=["POST"])
def upload_file():
    print("📤 UPLOAD")

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file and allowed_file(file.filename):
        task_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        input_filename = f"{task_id}_{filename}"
        output_filename = f"{task_id}_model.glb"

        input_path = os.path.join(app.config["UPLOAD_FOLDER"], input_filename)
        output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)

        file.save(input_path)

        thread = threading.Thread(target=process_blueprint_async, args=(task_id, input_path, output_path))
        thread.daemon = True
        thread.start()

        processing_status[task_id] = {"status": "queued", "progress": 0}
        return jsonify({"task_id": task_id, "message": "Processing started"}), 200

    return jsonify({"error": "Invalid file"}), 400

@app.route("/api/status/<task_id>", methods=["GET"])
def get_status(task_id):
    if task_id not in processing_status:
        return jsonify({"status": "error", "progress": 0, "error": "Task not found"}), 200
    return jsonify(processing_status[task_id])

@app.route("/api/download/<filename>")
def download_model(filename):
    try:
        return send_from_directory(app.config["OUTPUT_FOLDER"], filename)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    print("🚀 SIMPLE WORKING SERVER")
    app.run(debug=True, host="0.0.0.0", port=5000)

