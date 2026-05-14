import os
import uuid
import threading
from flask import Flask, request, render_template, jsonify, send_file
from video_creator import generate_video_task

app = Flask(__name__)
# Simple in‑memory job store (for demo; in production use Redis)
jobs = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/generate", methods=["POST"])
def start_generation():
    data = request.get_json()
    prompt = data.get("prompt")
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "progress": 0, "result": None}
    
    def background_work():
        try:
            # Update progress steps (optional)
            jobs[job_id]["progress"] = 10
            result = generate_video_task(prompt, job_id)
            jobs[job_id]["progress"] = 100
            jobs[job_id]["status"] = result["status"]
            jobs[job_id]["result"] = result
        except Exception as e:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["result"] = {"error": str(e)}
    
    thread = threading.Thread(target=background_work)
    thread.start()
    return jsonify({"job_id": job_id})

@app.route("/api/status/<job_id>")
def get_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({
        "status": job["status"],
        "progress": job.get("progress", 0),
        "result": job.get("result")
    })

@app.route("/api/download/<job_id>")
def download_video(job_id):
    job = jobs.get(job_id)
    if not job or job["status"] != "completed":
        return "Video not ready", 404
    video_path = job["result"].get("video_path")
    if not video_path or not os.path.exists(video_path):
        return "File missing", 404
    return send_file(video_path, as_attachment=True, download_name="generated_video.mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)