# 🖐️ Hand Gesture Control System (Windows)

Ek complete computer-vision system jo aapke laptop camera se haath ke gestures detect karke **Mouse cursor**, **Left click**, **System volume**, aur **PowerPoint / PDF presentation slides** ko control karta hai.

---

## 🔍 Pipeline Kaise Kaam Karti Hai? (How it works)

```
[Webcam (Live Video Feed)]
          │
          ▼
[OpenCV (cv2.flip & Frame Grab)]  ──> Mirror effect deta hai (aapka daayan haath screen pe daayan dikhta hai)
          │
          ▼
[MediaPipe Hands (21 Landmarks)] ──> Haath ke 21 keypoints (x, y, z) accurate detect karta hai
          │
          ▼
[Gesture Logic (gestures.py)]     ──> Ungliyon ki positions, distances aur swipe velocity analyze karta hai
          │
          ▼
[Mode State Machine + Debounce]   ──> Fist (Pause) / Mouse / Volume / Slide modes ko bina conflict switch karta hai
          │
          ▼
[OS Controllers (pyautogui/pycaw)]──> Windows cursor movement, click, master volume aur arrow keys press karta hai
          │
          ▼
[On-Screen HUD Display]           ──> Live FPS counter, active zone box, volume bar aur mode status video par dikhata hai
```

---

## 🚀 Installation & Setup Guide (Windows)

### 1. Prerequisites
- Windows 10 ya 11
- Python installed (Python 3.10, 3.11, ya 3.12+ recommended)
- Working laptop webcam

### 2. Steps to install and run

Open your PowerShell ya Command Prompt is folder ke andar:

```powershell
# Step 1: Virtual environment create karein (optional but recommended)
py -m venv venv

# Step 2: Virtual environment activate karein
.\venv\Scripts\activate

# Step 3: Required packages install karein
pip install -r requirements.txt

# Step 4: Unit tests run karke verify karein
pytest tests/

# Step 5: Main application start karein
python main.py
```

> **Window band karne ke liye:** Video window par click karke keyboard ka **ESC** button dabayein.

---

## 📋 Gesture Cheat-Sheet Table

Ye table aapko batayegi ki kaunsa gesture kya action perform karta hai:

| Gesture Name | Haath ki Position | Active Mode | Kya Action Hoga? |
|---|---|---|---|
| **Closed Fist (Mutthi)** | Saari ungliyan band (fist) | **PAUSE** | Sabkuch pause! Koi mouse ya volume move nahi hoga. (Safety first) |
| **Index Finger Up** | Sirf Index (pehli) ungli khadi, baaki band | **MOUSE** | Screen par mouse cursor move hoga (Active zone ke hisaab se). |
| **Index + Middle Pinch/Close** | Index aur Middle ungliyan ek saath paas layein | **MOUSE** | **Left Click** trigger hoga (with 0.3s cooldown). |
| **Thumb + Index Pinch** | Angootha aur Index ungli khol kar distance badhayein/ghatayein | **VOLUME** | Dono ungliyon ke distance se Windows ka **Master Volume** (0% - 100%) set hoga. |
| **Two Fingers Apart / Fast Swipe** | Index & Middle khuli hui + dur, ya tez haath hilana | **SLIDE** | Presentation me **Next Slide (`Right Arrow`)** ya **Previous Slide (`Left Arrow`)**. |

---

## ⚙️ How to Tune `config.py` (Custom Settings)

Agar aapko cursor ki speed, smoothness ya sensitivity change karni ho, toh `config.py` file open karke ye parameters change karein:

```python
# 1. Camera Resolution
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# 2. Mouse Smoothing
# Zyada number (e.g. 7.0) = zyada smooth par thoda slow; 
# Kam number (e.g. 3.0) = tez cursor par thoda jitter.
MOUSE_SMOOTHENING = 5.0

# 3. Active Zone Box Size
# Agar margin badhayenge (e.g. 120), toh chhota haath hilane par bhi cursor poori screen cover karega.
ACTIVE_ZONE_MARGIN_X = 100
ACTIVE_ZONE_MARGIN_Y = 80

# 4. Click Sensitivity
# Kitne pixels paas aane par click ho (default 38.0 pixels)
CLICK_DISTANCE_THRESHOLD = 38.0
CLICK_COOLDOWN = 0.3  # Ek click ke baad kitna wait kare (seconds)

# 5. Volume Pinch Range
PINCH_MIN_DIST = 25.0   # 0% volume jab ungliyan judi hon
PINCH_MAX_DIST = 160.0  # 100% volume jab ungliyan door hon

# 6. Slide Cooldown
SLIDE_COOLDOWN = 1.0    # Ek slide change ke baad 1 second ka delay
```

---

## 🛠️ Troubleshooting Guide

Agar koi issue aaye, toh is table ko check karein:

| Problem / Issue | Wajah (Reason) | Solution (Aasan Hal) |
|---|---|---|
| **Cursor Jitter / Kaanp raha hai** | Haath thoda shake hota hai ya lighting flickering hai. | `config.py` me `MOUSE_SMOOTHENING = 7.0` ya `8.0` kar dein. Isse cursor smooth ho jayega. |
| **Lag / Low FPS (< 15 FPS)** | CPU heavy ho raha hai ya camera resolution bohot high hai. | `config.py` me resolution `640x480` hi rakhein, aur laptop ko charger se connect karein taaki full performance mile. |
| **Wrong Gesture Detect ho raha hai** | Haath camera ke bohot paas ya bohot door hai. | Haath ko camera se lagbhag 1.5 se 2.5 feet door rakhein taaki poori palm clearly dikhe. |
| **Low Light / Andhera** | Camera haath ke landmarks detect nahi kar pa raha. | Room ki light on karein ya chehre/haath par saamne se light aane dein. Background dark ho toh better result milta hai. |
| **Camera Not Opening Error** | Dusra app (Zoom, Teams, Chrome) camera use kar raha hai, ya index galat hai. | Baaki camera apps close karein. Agar external camera hai toh `config.py` me `CAMERA_INDEX = 1` try karein. |
| **Volume Change Nahi Ho Raha** | Windows Audio Endpoint activate nahi hua ya permission issue. | Make sure `pycaw` aur `comtypes` installed hain (`pip install pycaw comtypes`). Sound card active ho (mute na ho). |
| **Antivirus / Window Safety Warning** | PyAutoGUI mouse move kar raha hai isliye system restrict kar sakta hai. | Terminal ko **Run as Administrator** karke chalaayein agar cursor kisi system window par na hile. |

---

## 💡 Ideas to Extend (Future Upgrades)

Aap is project ko aage aur powerful bana sakte hain:
1. **Two-Finger Scroll Gesture:**
   Index aur Middle finger ko up-down move karke web pages ya PDF scroll karwayein (`pyautogui.scroll()`).
2. **Instant Screenshot:**
   Thumb, index aur pinky ko extend karke (Rock/Spider-Man sign) screen capture lein aur Desktop par save karein.
3. **Screen Brightness Control:**
   `screen_brightness_control` python library use karke doosre haath se display brightness adjust karein.
4. **Two-Hand Zoom In / Zoom Out:**
   MediaPipe ko `max_num_hands=2` set karke dono haathon ke beech ka distance map karein (`Ctrl +` aur `Ctrl -` for zooming photos).
5. **Custom Deep Learning Classifier:**
   Haath ke landmark coordinates save karke ek chhota Random Forest ya PyTorch model train karein custom gestures ke liye.

---

## 📌 5-Line Quick Start Summary

1. Command Prompt kholein aur project directory me jayein: `cd c:\Users\mohdm\Desktop\HandGestureControl`
2. Environment activate karke run karein: `.\venv\Scripts\activate` aur fir `python main.py`
3. **Pehla Gesture (Mouse):** Sirf Index finger up karein aur haath hila kar cursor move karein.
4. **Doosra Gesture (Click):** Index aur Middle fingers ko paas layein left click karne ke liye.
5. **Volume & Slides:** Angootha + Index se pinch karke volume adjust karein, ya fast swipe karke slides change karein; kisi bhi waqt mutthi (closed fist) band karke sab pause kar dein!
