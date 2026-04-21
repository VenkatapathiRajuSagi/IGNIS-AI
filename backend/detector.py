import cv2
import time
import threading
from ultralytics import YOLO
import os
import numpy as np
from datetime import datetime
from backend.alerts.sms import send_fire_sms
from backend.alerts.voice import play_voice_alert
from backend.database import log_alert

class FireDetector:
    def __init__(self, model_path="models/fire_weight.pt", confidence_threshold=0.5, cooldown=5):
        self.conf_threshold = confidence_threshold
        self.cooldown = cooldown
        self.last_alert_time = 0
        self.is_running = False
        
        # Performance Throttling
        self.frame_count = 0
        self.fire_skip_rate = 2   # Run fire AI every 2nd frame (~15 FPS)
        self.safety_skip_rate = 8 # Run human AI every 8th frame
        
        # Cached results for smooth UI
        self.last_fire_boxes = []
        self.last_person_boxes = []
        self.last_fire_status = (False, 0.0, "Fire")
        
        # State Management
        self.fire_frame_threshold = 3 
        self.consecutive_fire_frames = 0
        self.prev_mask = None
        self.prev_gray_small = None # Downsampled for speed
        
        # Calibration & Stability
        self.is_steady = False
        self.calibration_frames = 0
        self.calibration_limit = 30 # ~1.5s
        self.bg_noise_mask = None
        
        self.local_only = False
        
        # Load Models
        print("📥 Initializing Optimization Engine...")
        try:
            self.model = YOLO(model_path)
            self.model.to('cpu') # Explicit for Mac stability
        except:
            self.model = YOLO("yolov8n.pt")
            
        try:
            self.safety_model = YOLO("yolov8n.pt")
            self.safety_model.to('cpu')
        except:
            self.safety_model = None

        self.source = os.getenv("VIDEO_SOURCE", 0)
        try: self.source = int(self.source)
        except: pass

    def start(self):
        self.is_running = True
        self.calibration_frames = 0 # Reset on start

    def stop(self):
        self.is_running = False

    def detect_global_motion(self, frame):
        """Ultra-fast motion detection on downsampled frame."""
        # Scale down to 160p for speed
        small = cv2.resize(frame, (160, 120), interpolation=cv2.INTER_LINEAR)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        
        if self.prev_gray_small is None:
            self.prev_gray_small = gray
            return 0
        
        diff = cv2.absdiff(self.prev_gray_small, gray)
        thresh = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)[1]
        motion_pct = (cv2.countNonZero(thresh) / (160 * 120)) * 100
        
        self.prev_gray_small = gray
        return motion_pct

    def detect_fire_hsv(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_fire = np.array([0, 140, 180])
        upper_fire = np.array([30, 255, 255])
        mask = cv2.inRange(hsv, lower_fire, upper_fire)
        
        if self.bg_noise_mask is not None:
            mask = cv2.bitwise_and(mask, cv2.bitwise_not(self.bg_noise_mask))
            
        fire_px = cv2.countNonZero(mask)
        pct = (fire_px / (frame.shape[0] * frame.shape[1])) * 100
        
        if pct < 0.4: return False, 0, mask

        # Fast Flicker
        flicker = 0
        if self.prev_mask is not None and self.prev_mask.shape == mask.shape:
            flicker = (cv2.countNonZero(cv2.absdiff(mask, self.prev_mask)) / (fire_px + 1)) * 100
        
        self.prev_mask = mask.copy()
        is_fire = (pct > 0.8) and (flicker > 6)
        return is_fire, pct, mask

    def process_frame(self, frame):
        if not self.is_running or frame is None:
            return frame, False, 0.0

        self.frame_count += 1
        
        # 1. Faster Stability Check
        motion = self.detect_global_motion(frame)
        self.is_steady = motion < 4.0 # Slightly more tolerant
        
        # 2. Calibration
        if self.calibration_frames < self.calibration_limit:
            self.calibration_frames += 1
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            c_mask = cv2.inRange(hsv, np.array([0, 100, 150]), np.array([35, 255, 255]))
            if self.bg_noise_mask is None: self.bg_noise_mask = c_mask
            else: self.bg_noise_mask = cv2.bitwise_or(self.bg_noise_mask, c_mask)
            
            cv2.putText(frame, "CALIBRATING...", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            return frame, False, 0.0

        if not self.is_steady:
            cv2.putText(frame, "CAMERA MOVING", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            return frame, False, 0.0

        # 3. Throttled Human Detection (Every 8th frame)
        if self.safety_model and (self.frame_count % self.safety_skip_rate == 0):
            self.last_person_boxes = []
            res = self.safety_model.predict(frame, conf=0.4, verbose=False)
            for r in res:
                for b in r.boxes:
                    if int(b.cls[0].item()) == 0:
                        self.last_person_boxes.append(b.xyxy[0].tolist())

        # 4. Throttled Fire Detection (Every 2nd frame)
        detected, max_conf, alert_type = self.last_fire_status
        if self.frame_count % self.fire_skip_rate == 0:
            detected, max_conf = False, 0.0
            self.last_fire_boxes = []
            if self.model:
                res = self.model.predict(frame, conf=self.conf_threshold, verbose=False)
                for r in res:
                    for b in r.boxes:
                        conf, cls = b.conf[0].item(), int(b.cls[0].item())
                        if conf > self.conf_threshold:
                            x1, y1, x2, y2 = b.xyxy[0].tolist()
                            # Suppression
                            if any(not (x2 < p[0] or x1 > p[2] or y2 < p[1] or y1 > p[3]) for p in self.last_person_boxes):
                                continue
                            
                            max_conf = max(max_conf, conf)
                            alert_type = "Fire" if cls == 0 else "Smoke" if cls == 2 else "Fire"
                            detected = True
                            self.last_fire_boxes.append({"box": [x1, y1, x2, y2], "type": alert_type, "conf": conf})
            
            # HSV Fallback logic inside the throttle to maintain sync
            if not detected:
                h_fire, h_pct, _ = self.detect_fire_hsv(frame)
                if h_fire and h_pct > 10.0: # Very strict fallback
                    detected, max_conf, alert_type = True, 0.5, "Heat"
            
            self.last_fire_status = (detected, max_conf, alert_type)

        # Draw Labels (Every frame for smoothness)
        for fb in self.last_fire_boxes:
            b, t, c = fb["box"], fb["type"], fb["conf"]
            color = (0,0,255) if t=="Fire" else (128,128,128)
            cv2.rectangle(frame, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), color, 3)
            cv2.putText(frame, f"{t} {c:.2f}", (int(b[0]), int(b[1])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
        for p in self.last_person_boxes:
            cv2.rectangle(frame, (int(p[0]), int(p[1])), (int(p[2]), int(p[3])), (255, 0, 0), 1)

        # Trigger logic (with Persistence to handle minor AI flickers)
        if detected:
            self.consecutive_fire_frames += 1
            if self.consecutive_fire_frames % 5 == 0:
                print(f"📡 High-Confidence Detection ongoing... ({self.consecutive_fire_frames} frames)")
        else:
            if self.consecutive_fire_frames > 0:
                self.consecutive_fire_frames -= 1
        
        if self.consecutive_fire_frames >= self.fire_frame_threshold:
            self.trigger_alerts(max_conf, alert_type, frame)

        cv2.putText(frame, "MONITORING...", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        return frame, detected, max_conf

    def trigger_alerts(self, confidence, alert_type, frame):
        t = time.time()
        elapsed = t - self.last_alert_time
        
        if elapsed > self.cooldown:
            self.last_alert_time = t
            now = datetime.now()
            path = f"captured_events/{alert_type.lower()}_{now.strftime('%H%M%S')}.jpg"
            if not os.path.exists("captured_events"): os.makedirs("captured_events")
            cv2.imwrite(path, frame)
            
            print(f"🔥 ALERT TRIGGERED: {alert_type} (Conf: {confidence:.2f})")
            log_alert(confidence, alert_type, image_path=path)
            
            # Use native afplay in a thread
            threading.Thread(target=play_voice_alert, daemon=True).start()
            
            if not self.local_only:
                threading.Thread(target=send_fire_sms, args=(confidence, now.strftime("%Y-%m-%d %H:%M:%S"), alert_type), daemon=True).start()
            
            # Post-alert "Soft Reset" for freshness
            self.prev_mask = None 
            self.consecutive_fire_frames = self.fire_frame_threshold - 1 # Prime for next trigger
        else:
            # Helpful logging for the presenter
            remaining = int(self.cooldown - elapsed)
            if self.frame_count % 30 == 0:
                 print(f"⏳ Fire Present - Cooldown... ({remaining}s remaining)")
