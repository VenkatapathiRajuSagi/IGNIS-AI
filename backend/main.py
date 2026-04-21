import cv2
import os
from fastapi import FastAPI, Response, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from backend.detector import FireDetector
from backend.database import init_db, get_recent_alerts
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Wildfire Detection System")

# Initialize DB
init_db()

# Setup Static and Templates
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(frontend_dir, "templates"))

# Initialize Detector
detector = FireDetector(
    confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", 0.5)),
    cooldown=int(os.getenv("ALERT_COOLDOWN_SECONDS", 5))
)

# Shared Camera State
class CameraState:
    def __init__(self):
        self.cap = None
        self.is_active = False

camera_state = CameraState()

def gen_frames():
    """Video streaming generator function using the real camera."""
    camera_state.cap = cv2.VideoCapture(detector.source)
    camera_state.is_active = True
    
    if not camera_state.cap.isOpened():
        print(f"❌ Could not open video source {detector.source}")
    
    # Grace period (approx 1-2 seconds) to allow camera hardware to stabilize
    # (prevents false alerts from auto-exposure flashes at startup)
    while camera_state.is_active:
        success, frame = camera_state.cap.read()
        if not success:
            continue
        
        # Run detection (Calibration & Stability are handled inside process_frame)
        processed_frame, detected, conf = detector.process_frame(frame)
        
        if processed_frame is None:
            processed_frame = frame
        
        if processed_frame is None:
            continue

        # Encode for Streaming
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    if camera_state.cap:
        camera_state.cap.release()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(gen_frames(),
                             media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/alerts")
async def get_alerts():
    alerts = get_recent_alerts()
    return [{"id": a.id, "timestamp": a.timestamp.strftime("%Y-%m-%d %H:%M:%S"), 
             "confidence": f"{a.confidence:.2f}", "type": a.alert_type} for a in alerts]

@app.get("/api/status")
async def get_status():
    return {
        "status": "Active" if detector.is_running else "Paused",
        "video_source": detector.source,
        "is_steady": detector.is_steady,
        "calibration": detector.calibration_frames * 100 // detector.calibration_limit if detector.calibration_frames < detector.calibration_limit else 100
    }

@app.delete("/api/reset_history")
async def reset_history():
    from backend.database import SessionLocal, AlertLog
    db = SessionLocal()
    try:
        db.query(AlertLog).delete()
        db.commit()
        return {"status": "success"}
    finally:
        db.close()

class SettingsUpdate(BaseModel):
    threshold: float
    is_running: bool

@app.post("/api/settings")
async def update_settings(settings: SettingsUpdate):
    detector.conf_threshold = settings.threshold
    if settings.is_running:
        detector.start()
        # Note: If is_active is already True, gen_frames will handle it.
        # This implementation ensures the generator stops if is_running is False.
    else:
        detector.stop()
        camera_state.is_active = False # Stop the camera loop
    
    return {"message": "Settings updated", "is_running": detector.is_running}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
