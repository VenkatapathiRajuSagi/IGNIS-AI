import os
import subprocess
from gtts import gTTS

# Telugu alert message
TELUGU_ALERT_TEXT = "అగ్ని ప్రమాదం గుర్తించబడింది, దయచేసి జాగ్రత్తగా ఉండండి"
AUDIO_FILE = "fire_alert_te.mp3"

def generate_alert_audio():
    """Generates the Telugu alert audio file if it doesn't exist."""
    if not os.path.exists(AUDIO_FILE):
        print("📥 Generating Telugu alert audio...")
        try:
            tts = gTTS(text=TELUGU_ALERT_TEXT, lang='te')
            tts.save(AUDIO_FILE)
            print(f"✅ Audio saved as {AUDIO_FILE}")
        except Exception as e:
            print(f"❌ Failed to generate audio: {e}")

def play_voice_alert():
    """Plays the audio using native macOS afplay (Conflict-Free)."""
    generate_alert_audio()
    
    if not os.path.exists(AUDIO_FILE):
        print("⚠️ Alert audio missing.")
        return

    try:
        # Using afplay (native Mac) instead of pygame to avoid library conflicts
        # This is a non-blocking background process
        print("🔊 Playing Voice Alert (Native)...")
        subprocess.Popen(["afplay", AUDIO_FILE])
    except Exception as e:
        print(f"❌ Failed to play audio via afplay: {e}")

# Pre-generate on load
generate_alert_audio()
