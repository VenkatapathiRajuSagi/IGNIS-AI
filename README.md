# 🚨 IGNIS AI: Advanced Wildfire Detection & Alert System 🛸

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![YOLOv8](https://img.shields.io/badge/AI-YOLOv8-red.svg)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green.svg)
![Status](https://img.shields.io/badge/Status-Project_Ready-brightgreen.svg)

**IGNIS** is a high-performance, real-time wildfire detection system powered by Computer Vision. Designed for mission-critical monitoring, it combines deep learning object detection with advanced heuristic verification to provide accurate, multi-channel alerts while maintaining a near-zero false positive rate.

## 🌟 Key Features

### 🕵️‍♂️ Dual-Layer AI Detection
- **Specialized Fire Model**: Powered by a custom-trained YOLOv8 model dedicated to identifying flames and smoke in diverse environmental conditions.
- **Human Suppression Logic**: Integrated "Safety Guard" AI that identifies humans and automatically suppresses false alerts caused by skin tones or clothing.

### 🛡️ Presentation-Grade Stability
- **Anti-Shake Protection**: Detects "Global Motion" (camera shakes/laptop movement) and pauses detection to prevent motion-blur false positives.
- **Environmental Calibration**: Automically learns the background room noise for 2 seconds on startup to ignore stationary red/orange objects (fire extinguishers, exit signs).
- **Detection Persistence**: Intelligent "Memory" logic that maintains fire tracking even during brief video flickers or lighting changes.

### 📢 Multi-Channel Alerting
- **Telugu Voice Alerts**: Instant audio notifications in Telugu using native macOS speech.
- **SMS Notifications**: Automated emergency SMS alerts sent via Twilio with detection confidence levels.
- **Cloud Logging**: Automatic snapshot capture and database logging of every fire event.

## 🍱 Project Architecture

- **Backend**: FastAPI (Python)
- **Vision Engine**: OpenCV & Ultralytics YOLOv8
- **Frontend**: Glassmorphism Dashboard (Vanilla JS & HTML5)
- **Database**: SQLAlchemy (SQLite)

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- macOS (Optimized for `afplay` audio)

### 2. Setup
```bash
# Activate Environment
source venv/bin/activate

# Install Dependencies
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file with your credentials:
```env
VIDEO_SOURCE=0
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=your_number
ALERT_PHONE_NUMBER=your_target_phone
```

### 4. Run
```bash
python3 run.py
```

## 🧠 Dataset & Weights
This repository includes the pre-trained weights in the `models/` folder:
- `fire_weight.pt`: Professional wildfire detection model.
- `yolov8n.pt`: Base safety model for human detection.

---
*Developed for the Advanced Wildfire Monitoring Event 2026.*
