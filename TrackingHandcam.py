import cv2 as cv #OpenCV is used for the Live webcam feed.
import mediapipe as mp #this is used for hand tracking
import time #This is for calculating the FPS of the hand tracking to see how well it performs on my computer.
import mouse #This is the main library i will be using to control the mouse.
import ctypes # i ma use this to get the screen resolution to better map the hand to mouse.
import math #this is used to calculate the distance between the thumb and index finger to determine when to click.
import tkinter as tk
import threading
import os


#Ts was slightly hard to understand but i got it cuz i am him
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

#intilizing all the globle variables here. 
latest_result = None
user32=ctypes.windll.user32
screen_width, screen_height = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
SmoothX, SmoothY = 0, 0
framepercentw = 0.30
framepercenth = 0.30
ispressed = False
slowthreshold = 0.45
pressthreshold = 0.25
is_paused = True
app_running = True
clicktime = 0 
show_preview = True
detected_camera_idx = 0
#pressthresholdrightclick = 0.015
#releasethreshold = 0.10

def print_result(result: HandLandmarker, output_image: mp.Image, timestamp_ms: int):
    global latest_result
    latest_result = result

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='hand_landmarker.task'),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=print_result,
    min_hand_detection_confidence=0.6,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.7,
    num_hands=1 
)

def get_camera():
    """Detect and connect to an active camera with DirectShow fallback."""
    # DirectShow (fastest on Windows)
    for idx in [0, 1, 2]:
        c = cv.VideoCapture(idx, cv.CAP_DSHOW)
        if c.isOpened():
            ret, test_frame = c.read()
            if ret and test_frame is not None and test_frame.mean() > 2.0:
                c.set(cv.CAP_PROP_FRAME_WIDTH, 640)
                c.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
                c.set(cv.CAP_PROP_FPS, 60)
                print(f"[H.A.N.D.] Connected to Camera {idx} using CAP_DSHOW")
                return c, idx
            c.release()

    # Fallback to default backend
    for idx in [0, 1, 2]:
        c = cv.VideoCapture(idx)
        if c.isOpened():
            ret, test_frame = c.read()
            if ret and test_frame is not None and test_frame.mean() > 2.0:
                c.set(cv.CAP_PROP_FRAME_WIDTH, 640)
                c.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
                c.set(cv.CAP_PROP_FPS, 60)
                print(f"[H.A.N.D.] Connected to Camera {idx} using default backend")
                return c, idx
            c.release()

    return None, -1

def tracking_thread():
    global SmoothX, SmoothY, ispressed, app_running, is_paused, clicktime, show_preview, detected_camera_idx
    with HandLandmarker.create_from_options(options) as landmarker:
        cap, detected_camera_idx = get_camera()
        if cap is None:
            print("[H.A.N.D.] ERROR: No active camera detected!")
            if 'root' in globals() and 'status_label' in globals():
                root.after(0, lambda: status_label.config(text="Status: No Camera Found!", fg="red"))
            return

        if 'root' in globals() and 'camera_label' in globals():
            root.after(0, lambda: camera_label.config(text=f"Camera: Index {detected_camera_idx} (Active)"))

        last_timestamp_ms = 0

        while cap.isOpened() and app_running:
            success, frame = cap.read()
            if not success:
                time.sleep(0.01)
                continue

            frame = cv.flip(frame, 1)
            h, w, _ = frame.shape

            # Mouse mapping box overlay dimensions
            box_x1 = int(w * framepercentw)
            box_y1 = int(h * framepercenth)
            box_x2 = int(w * (1 - framepercentw))
            box_y2 = int(h * (1 - framepercenth))

            if is_paused:
                if show_preview:
                    # Draw paused indicator and mapping box
                    cv.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), (180, 180, 180), 1)
                    cv.putText(frame, "PAUSED - Click 'Start Tracking' in GUI", (15, 30),
                               cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                    cv.imshow("H.A.N.D. - Camera Feed", frame)
                    key = cv.waitKey(1) & 0xFF
                    # Terminate if user pressed ESC, 'q', or clicked the 'X' button on the camera feed window
                    if key in (27, ord('q')) or (cv.getWindowProperty("H.A.N.D. - Camera Feed", cv.WND_PROP_VISIBLE) < 1):
                        request_exit()
                        break
                time.sleep(0.03)
                continue
            rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
            current_timestamp_ms = int(time.time() * 1000)
            if current_timestamp_ms <= last_timestamp_ms:
                current_timestamp_ms = last_timestamp_ms + 1
            last_timestamp_ms = current_timestamp_ms

            landmarker.detect_async(mp_image, current_timestamp_ms)

            # Draw mouse mapping region
            cv.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2), (255, 120, 0), 2)
            cv.putText(frame, "Mouse Region", (box_x1 + 5, box_y1 + 18), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 120, 0), 1)

            if latest_result and latest_result.hand_landmarks:
                landmarks = latest_result.hand_landmarks[0]
                palm_area = math.hypot(landmarks[0].x - landmarks[9].x, landmarks[0].y - landmarks[9].y)
                if palm_area < 0.00000001:
                    palm_area = 0.00000001
                pinch_gap_index = math.hypot(landmarks[8].x - landmarks[4].x, landmarks[8].y - landmarks[4].y)
                pinch_gap_middle = math.hypot(landmarks[12].x - landmarks[4].x, landmarks[12].y - landmarks[4].y)
                pinch_gap_ring = math.hypot(landmarks[16].x - landmarks[4].x, landmarks[16].y - landmarks[4].y)
                pinch_ratio_index = pinch_gap_index / palm_area
                pinch_ratio_middle = pinch_gap_middle / palm_area
                pinch_ratio_ring = pinch_gap_ring / palm_area

                # Draw landmarks on preview
                knuckle = (int(landmarks[9].x * w), int(landmarks[9].y * h))
                thumb_pt = (int(landmarks[4].x * w), int(landmarks[4].y * h))
                index_pt = (int(landmarks[8].x * w), int(landmarks[8].y * h))
                middle_pt = (int(landmarks[12].x * w), int(landmarks[12].y * h))
                ring_pt = (int(landmarks[16].x * w), int(landmarks[16].y * h))

                cv.circle(frame, knuckle, 6, (0, 255, 255), -1)
                for pt in [thumb_pt, index_pt, middle_pt, ring_pt]:
                    cv.circle(frame, pt, 5, (255, 255, 0), -1)

                idx_col = (0, 255, 0) if pinch_ratio_index < pressthreshold else (100, 100, 255)
                mid_col = (255, 0, 0) if pinch_ratio_middle < pressthreshold else (100, 100, 255)
                ring_col = (0, 0, 255) if pinch_ratio_ring < pressthreshold else (100, 100, 255)

                cv.line(frame, thumb_pt, index_pt, idx_col, 2)
                cv.line(frame, thumb_pt, middle_pt, mid_col, 2)
                cv.line(frame, thumb_pt, ring_pt, ring_col, 2)

                rawX = landmarks[9].x * screen_width
                rawY = landmarks[9].y * screen_height
                MappedX = int((rawX - (screen_width * framepercentw)) * (screen_width / (screen_width * (1 - 2 * framepercentw))))
                MappedY = int((rawY - (screen_height * framepercenth)) * (screen_height / (screen_height * (1 - 2 * framepercenth))))

                # Clamp mapped coordinates to display boundaries
                MappedX = max(0, min(screen_width - 1, MappedX))
                MappedY = max(0, min(screen_height - 1, MappedY))

                distance_to_target = math.hypot(SmoothX - MappedX, SmoothY - MappedY)

                # Determine if an action gesture is actively engaged or in progress (click, right-click, or dragging)
                action_in_progress = (pinch_ratio_index < pressthreshold or 
                                      pinch_ratio_middle < pressthreshold or 
                                      pinch_ratio_ring < pressthreshold)
                action_active = ispressed or action_in_progress

                # Focus mode (slow precision mode) is disabled whenever any action is active
                focus_mode_active = (not action_active) and (pinch_ratio_index < slowthreshold or pinch_ratio_middle < slowthreshold)

                if focus_mode_active:
                    SmootheningFactor = 0.02
                else:
                    if distance_to_target < 15:
                        SmootheningFactor = 0.05
                    else:
                        SmootheningFactor = 0.30

                SmoothX = SmoothX + (MappedX - SmoothX) * SmootheningFactor
                SmoothY = SmoothY + (MappedY - SmoothY) * SmootheningFactor
                mouse.move(int(SmoothX), int(SmoothY), absolute=True, duration=0)

                if pinch_ratio_index < pressthreshold:
                    if not ispressed:
                        current_time = time.time()
                        if current_time - clicktime < 0.4:
                            mouse.double_click()
                            clicktime = 0
                            ispressed = True
                            print(f"Double Clicked (Ratio: {pinch_ratio_index:.2f})")
                        else:
                            mouse.click() 
                            clicktime = current_time
                            ispressed = True
                            print(f"Left Clicked (Ratio: {pinch_ratio_index:.2f})")

                elif pinch_ratio_middle < pressthreshold:
                    if not ispressed:
                        mouse.right_click()
                        ispressed = True
                        print("Right Clicked")
                        print(f"Right Clicked (Ratio: {pinch_ratio_middle:.2f})")
                elif pinch_ratio_ring < pressthreshold:
                    if not ispressed:
                        mouse.press()
                        ispressed = True
                        print(f"Dragging (Ratio: {pinch_ratio_ring:.2f})")
                else:
                    if ispressed:
                        mouse.release()
                        ispressed = False
                        print("released")
            else:
                focus_mode_active = False
                # Safety release if tracking is lost while holding an action (e.g. dragging)
                if ispressed:
                    mouse.release()
                    ispressed = False
                    print("[H.A.N.D.] Tracking lost while action active -> Safety released mouse")

            # Status overlays on preview
            cv.putText(frame, "TRACKING ACTIVE", (15, 30), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            if ispressed:
                cv.putText(frame, "ACTION ACTIVE", (15, 60), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            elif focus_mode_active:
                cv.putText(frame, "SLOW FOCUS MODE", (15, 60), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

            if show_preview:
                cv.imshow("H.A.N.D. - Camera Feed", frame)
                key = cv.waitKey(1) & 0xFF
                # Terminate if user pressed ESC, 'q', or clicked the 'X' button on the camera feed window
                if key in (27, ord('q')) or (cv.getWindowProperty("H.A.N.D. - Camera Feed", cv.WND_PROP_VISIBLE) < 1):
                    request_exit()
                    break

        cap.release()
        try:
            cv.destroyAllWindows()
        except Exception:
            pass

def check_tracking():
    global is_paused
    is_paused = not is_paused
    if is_paused:
        status_label.config(text="Status: Paused", fg="grey")
        toggle_button.config(text="Start Tracking") 
    else:
        status_label.config(text="Status: Tracking", fg="green")
        toggle_button.config(text="Pause Tracking")

def toggle_preview():
    global show_preview
    show_preview = preview_var.get()
    if not show_preview:
        try:
            cv.destroyWindow("H.A.N.D. - Camera Feed")
        except Exception:
            pass

def request_exit():
    """Trigger application termination from tracking thread or window event."""
    global app_running, ispressed
    if not app_running:
        return
    app_running = False
    if ispressed:
        try:
            mouse.release()
        except Exception:
            pass
        ispressed = False
    if 'root' in globals():
        try:
            root.after(0, on_closing)
        except Exception:
            pass

def on_closing():
    """Cleanly close all resources, wait for threads, and destroy UI."""
    global app_running, ispressed
    if not app_running:
        try:
            root.destroy()
        except Exception:
            pass
        return

    app_running = False
    if ispressed:
        try:
            mouse.release()
        except Exception:
            pass
        ispressed = False

    # Wait briefly for tracking thread to release camera and close OpenCV windows
    if 'tracking_thread_instance' in globals() and tracking_thread_instance.is_alive():
        tracking_thread_instance.join(timeout=0.6)

    try:
        cv.destroyAllWindows()
    except Exception:
        pass

    try:
        root.destroy()
    except Exception:
        pass

# Initiating GUI
root = tk.Tk()
root.title("H.A.N.D. - Hand Actuated Navigation Device")
root.geometry("340x220")
root.attributes("-topmost", True)

camera_label = tk.Label(root, text="Camera: Detecting...", fg="black", font=("Arial", 10))
camera_label.pack(pady=5)

status_label = tk.Label(root, text="Status: Paused", fg="grey", font=("Arial", 12, "bold"))
status_label.pack(pady=10)

toggle_button = tk.Button(root, text="Start Tracking", command=check_tracking, font=("Arial", 12), width=15)
toggle_button.pack(pady=5)

preview_var = tk.BooleanVar(value=True)
preview_check = tk.Checkbutton(root, text="Show Camera Preview Window", variable=preview_var, command=toggle_preview, font=("Arial", 10))
preview_check.pack(pady=10)

root.protocol("WM_DELETE_WINDOW", on_closing)

tracking_thread_instance = threading.Thread(target=tracking_thread, daemon=True)
tracking_thread_instance.start()

root.mainloop()

