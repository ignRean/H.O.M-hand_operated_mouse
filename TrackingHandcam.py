import cv2 as cv #OpenCV is used for the Live webcam feed.
import mediapipe as mp #this is used for hand tracking
import time #This is for calculating the FPS of the hand tracking to see how well it performs on my computer.
import mouse #This is the main library i will be using to control the mouse.
import ctypes # i ma use this to get the screen resolution to better map the hand to mouse.
import math #this is used to calculate the distance between the thumb and index finger to determine when to click.
import tkinter as tk
import threading
import os
import keyboard


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
pressthreshold = 0.17
dragthreshold= 0.12
is_paused = True
app_running = True
clicktime=0 
#pressthresholdrightclick = 0.015
#releasethreshold = 0.10

class OneEuroFilter:
    def __init__(self, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = 0.0
        self.dx_prev = 0.0
        self.t_prev = 0.0
        self.initialized = False

    def smoothing_factor(self, t_e, cutoff):
        r = 2 * math.pi * cutoff * t_e
        return r / (r + 1)

    def __call__(self, t, x):
        if not self.initialized:
            self.x_prev = x
            self.dx_prev = 0.0
            self.t_prev = t
            self.initialized = True
            return x
            
        t_e = t - self.t_prev
        if t_e <= 0.0:
            return x
            
        a_d = self.smoothing_factor(t_e, self.d_cutoff)
        dx = (x - self.x_prev) / t_e
        dx_hat = a_d * dx + (1 - a_d) * self.dx_prev
        
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self.smoothing_factor(t_e, cutoff)
        x_hat = a * x + (1 - a) * self.x_prev
        
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t
        return x_hat

#The print_result function is the callback function that will be called every time the hand landmarker has a new result. It takes in the result, the output image, and the timestamp of the frame. In this function, we simply update the latest_result variable with the new result so that we can use it in the tracking_thread function to control the mouse.
def print_result(result: HandLandmarker, output_image: mp.Image, timestamp_ms: int):
    global latest_result
    latest_result = result
#Here we are setting up the options for the hand landmarker. We specify the model asset path, the running mode (live stream), the callback function, and some confidence thresholds for hand detection, presence, and tracking. We also specify that we only want to track one hand to improve performance.
options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='hand_landmarker.task'),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=print_result,
    min_hand_detection_confidence=0.6,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.7,
    num_hands=1 
)
#I am using the live stream mode of the hand landmarker, which means that it will continuously process the frames from the webcam and call the print_result function with the latest results. The print_result function simply updates the latest_result variable with the latest hand landmarks detected by the model.
def tracking_thread():
    global SmoothX, SmoothY, ispressed, app_running, is_paused, clicktime
    
    # Initialize One Euro Filters for X and Y coordinates
    filter_x = OneEuroFilter(min_cutoff=0.1, beta=0.01)
    filter_y = OneEuroFilter(min_cutoff=0.1, beta=0.01)
    prev_scroll_y = None
    
    with HandLandmarker.create_from_options(options) as landmarker:
        cap = cv.VideoCapture(0)
        cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480) 
        cap.set(cv.CAP_PROP_FPS, 60)
        frame_timestamp_ms = 0
    
        while cap.isOpened() and app_running:
            if is_paused:
                cap.grab()
                time.sleep(0.03)
                continue
            success, frame = cap.read()
            if not success: continue
            frame = cv.flip(frame, 1)
            rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
            frame_timestamp_ms += 1
            landmarker.detect_async(mp_image, frame_timestamp_ms)
            if latest_result and latest_result.hand_landmarks:
                palm_area = math.hypot(latest_result.hand_landmarks[0][0].x - latest_result.hand_landmarks[0][9].x, latest_result.hand_landmarks[0][0].y - latest_result.hand_landmarks[0][9].y )
                if palm_area < 0.00000001:
                    palm_area = 0.00000001
                # Left click: Index Tip (8) to Thumb Tip (4)
                pinch_gap_leftclick= math.hypot(latest_result.hand_landmarks[0][8].x - latest_result.hand_landmarks[0][4].x, latest_result.hand_landmarks[0][8].y - latest_result.hand_landmarks[0][4].y)
                # Right click: Middle Tip (12) to Thumb Tip (4)
                pinch_gap_rightclick= math.hypot(latest_result.hand_landmarks[0][12].x - latest_result.hand_landmarks[0][4].x, latest_result.hand_landmarks[0][12].y - latest_result.hand_landmarks[0][4].y)
                # Drag: Ring Tip (16) to Thumb Tip (4)
                pinch_gap_drag= math.hypot(latest_result.hand_landmarks[0][16].x - latest_result.hand_landmarks[0][4].x, latest_result.hand_landmarks[0][16].y - latest_result.hand_landmarks[0][4].y)
                # Scroll: Pinky Tip (20) to Thumb Tip (4)
                pinch_gap_scroll = math.hypot(latest_result.hand_landmarks[0][20].x - latest_result.hand_landmarks[0][4].x, latest_result.hand_landmarks[0][20].y - latest_result.hand_landmarks[0][4].y)
                
                pinch_ratio_leftclick = pinch_gap_leftclick / palm_area
                pinch_ratio_rightclick = pinch_gap_rightclick / palm_area
                pinch_ratio_drag = pinch_gap_drag / palm_area
                pinch_ratio_scroll = pinch_gap_scroll / palm_area

                rawX= latest_result.hand_landmarks[0][5].x * screen_width
                rawY= latest_result.hand_landmarks[0][5].y * screen_height
                MappedX = int((rawX - (screen_width * framepercentw)) * (screen_width / (screen_width * (1 - 2 * framepercentw))))
                MappedY = int((rawY - (screen_height * framepercenth)) * (screen_height / (screen_height * (1 - 2 * framepercenth))))
                
                # Apply One Euro Filter to remove jitters without adding lag
                current_t = time.time()
                SmoothX = filter_x(current_t, MappedX)
                SmoothY = filter_y(current_t, MappedY)
                
                # Boundary clamping
                SmoothX = max(0, min(screen_width, SmoothX))
                SmoothY = max(0, min(screen_height, SmoothY))
                
                mouse.move(int(SmoothX), int(SmoothY), absolute=True, duration=0)
                #click function mi bomba
                if pinch_ratio_leftclick < pressthreshold:
                    if not ispressed:
                        current_time = time.time()
                        if current_time - clicktime < 0.4:
                            mouse.double_click()
                            clicktime = 0
                            print(f"Double Clicked (Ratio: {pinch_ratio_leftclick:.2f})")
                        else:
                            mouse.click() 
                            clicktime = current_time
                            ispressed = True
                            print(f"Left Clicked (Ratio: {pinch_ratio_leftclick:.2f})")
                #right clickty your property is my property
                elif pinch_ratio_rightclick < pressthreshold:
                    if not ispressed:
                        mouse.right_click()
                        ispressed = True
                        print("Right Clicked")
                        print(f"Right Clicked (Ratio: {pinch_ratio_rightclick:.2f})")
                #slay drag and drop like a boss
                elif pinch_ratio_drag < pressthreshold:
                    if not ispressed:
                        mouse.press()
                        ispressed = True
                        print(f"Dragging (Ratio: {pinch_ratio_drag:.2f})")
                elif pinch_ratio_scroll < pressthreshold:
                    if prev_scroll_y is not None:
                        scroll_delta = prev_scroll_y - MappedY
                        # Adjust scroll speed multiplier as needed
                        if abs(scroll_delta) > 2:
                            mouse.wheel(int(scroll_delta / 5))
                    prev_scroll_y = MappedY
                else:
                    prev_scroll_y = None
                    if ispressed:
                        mouse.release()
                        ispressed = False
                        print("released")
            
    cap.release()

def check_tracking():
    global is_paused
    is_paused = not is_paused
    if is_paused:
       status_label.config(text="Status: Paused", fg="grey")
       toggle_button.config(text="Start Tracking") 
    else:
         status_label.config(text="Status: Tracking", fg="green")
         toggle_button.config(text="Pause Tracking")

def on_closing():
    global app_running
    app_running = False
    root.destroy()
    os._exit(0)

#intiating that STUPID GUI AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH HELP I AM LOSING IT AHHHHHHHHHHHHHH

root=tk.Tk()
root.title("H.A.N.D. - Hand Actuated Navigation Device")
root.geometry("300x150")
root.attributes("-topmost", True)
status_label=tk.Label(root, text="Status: Paused", fg="grey", font=("Arial", 12))
status_label.pack(pady=20)
toggle_button=tk.Button(root, text="Start Tracking", command=check_tracking, font=("Arial", 12), width=15)
toggle_button.pack(pady=10)

root.protocol("WM_DELETE_WINDOW", on_closing)

tracking_thread_instance = threading.Thread(target=tracking_thread)
tracking_thread_instance.start()

# Register the global hotkey to pause/resume tracking
keyboard.add_hotkey('f8', lambda: root.after(0, check_tracking))

root.mainloop()

