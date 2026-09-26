# H.A.N.D. - Hand Actuated Navigation Device 🖐️🖱️
*(H.O.M. - Hand Operated Mouse)*

An AI-powered computer vision mouse controller built with Python, OpenCV, and MediaPipe. Control your cursor, left click, double click, right click, and drag files or windows using real-time hand gestures via your webcam—no physical mouse required.

---

## 🚀 Features

- **Real-Time Hand Tracking**: Uses Google MediaPipe's high-precision `HandLandmarker` model for low-latency hand detection.
- **Smart DirectShow Camera Detection**: Automatically scans and connects to available webcam devices (compatible with integrated webcams, USB cameras, and virtual cameras like DroidCam).
- **Proportional Screen Mapping & Smoothing**: Maps a comfortable region of the webcam feed to your full display resolution with adaptive exponential moving average (EMA) smoothing and target boundary clamping.
- **Slow Focus Mode (Precision Aiming)**: Automatically slows down cursor speed when fingers are brought close to the thumb, allowing pixel-perfect precision when aiming at small buttons and links.
- **Action-Aware Mode Switching**: Automatically disables focus mode during actions such as dragging, ensuring swift and responsive cursor control.
- **Full Mouse Gesture Set**:
  - **Cursor Move**: Move your hand inside the active camera region.
  - **Left Click**: Pinch index finger to thumb.
  - **Double Click**: Double pinch index finger to thumb within 400 ms.
  - **Right Click**: Pinch middle finger to thumb.
  - **Drag / Hold**: Pinch ring finger to thumb (holds left mouse down; release pinch to drop).
- **Failsafe Tracking Loss Protection**: Automatically releases held mouse buttons if your hand moves out of frame, preventing stuck drag states.
- **Clean Graphical Interface (Tkinter & OpenCV HUD)**:
  - Toggle tracking on/off.
  - Optional live camera preview window with visual landmarks and HUD state overlay (`TRACKING ACTIVE`, `ACTION ACTIVE`, `SLOW FOCUS MODE`).
  - Graceful multi-threaded shutdown via GUI close button, camera window close button, or <kbd>Esc</kbd> / <kbd>q</kbd>.

---

## 🛠️ Gesture Guide

| Gesture | Fingers Involved | Action | Description |
| :--- | :--- | :--- | :--- |
| **Move Cursor** | Palm / Hand | Move Cursor | Anchor tracks your knuckle to glide the cursor across the screen. |
| **Precision Focus** | Index / Middle near Thumb | Slow Focus Mode | Cursor slows down for precise alignment before clicking. |
| **Left Click** | Index + Thumb | Single Click | Tap index finger to thumb. |
| **Double Click** | Index + Thumb | Double Click | Tap index finger to thumb twice quickly (< 400 ms). |
| **Right Click** | Middle + Thumb | Right Click | Tap middle finger to thumb. |
| **Drag & Drop** | Ring + Thumb | Mouse Hold / Drag | Pinch ring finger to thumb to hold down left click; move your hand to drag, and release pinch to drop. |

---

## 📋 Requirements

- **Operating System**: Windows 10 / 11 (64-bit recommended)
- **Python**: Python 3.9 - 3.12 (MediaPipe compatibility)
- **Hardware**: Any standard USB, built-in, or virtual webcam (e.g. DroidCam)

---

## 📥 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/ignRean/H.O.M-hand_operated_mouse.git
cd H.O.M-hand_operated_mouse
```

### 2. Set Up a Virtual Environment (Recommended)
```bash
# Create a virtual environment
python -m venv venv

# Activate on Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
*Or install packages manually:*
```bash
pip install opencv-python mediapipe mouse
```

> [!NOTE]
> `tkinter` comes pre-installed with standard Python distributions on Windows.

### 4. Verify Model File
Ensure `hand_landmarker.task` is located in the root directory alongside `TrackingHandcam.py`. If missing, download it from [Google MediaPipe Hand Landmarker Task](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker).

---

## 🎮 How to Use

1. **Run the Application**:
   ```bash
   python TrackingHandcam.py
   ```
2. **Start Tracking**:
   - The GUI will launch with status **Paused** by default.
   - Position your hand comfortably in front of your camera.
   - Click **"Start Tracking"** in the GUI.
3. **Navigate & Gesture**:
   - Keep your hand within the orange **"Mouse Region"** box shown on the camera preview.
   - Pinch your index finger to click, middle finger to right-click, and ring finger to drag.
4. **Pause or Exit**:
   - Click **"Pause Tracking"** anytime in the GUI to temporarily stop cursor control.
   - To completely close the application, click the **'X'** on the GUI window, the **'X'** on the camera preview window, or press <kbd>Esc</kbd> / <kbd>q</kbd> while the preview window is focused.

---

## ⚙️ Configuration & Customization

Key parameters can be adjusted directly at the top of `TrackingHandcam.py`:

```python
framepercentw = 0.30     # Horizontal deadzone margin (lower = larger active area)
framepercenth = 0.30     # Vertical deadzone margin (lower = larger active area)
slowthreshold = 0.45     # Pinch ratio to trigger Slow Focus Mode
pressthreshold = 0.25    # Pinch ratio to trigger clicks and drags
```

---

## 📜 License

This project is open source and available under the [MIT License](LICENSE).
