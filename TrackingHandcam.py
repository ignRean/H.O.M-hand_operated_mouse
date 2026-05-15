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
clicktime=0 
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

def tracking_thread():
    global SmoothX, SmoothY, ispressed, app_running, is_paused, clicktime
    with HandLandmarker.create_from_options(options) as landmarker:
        cap = cv.VideoCapture(1)
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
                pinch_gap_index= math.hypot(latest_result.hand_landmarks[0][8].x - latest_result.hand_landmarks[0][4].x, latest_result.hand_landmarks[0][8].y - latest_result.hand_landmarks[0][4].y)
                pinch_gap_middle= math.hypot(latest_result.hand_landmarks[0][12].x - latest_result.hand_landmarks[0][4].x, latest_result.hand_landmarks[0][12].y - latest_result.hand_landmarks[0][4].y)
                pinch_gap_ring= math.hypot(latest_result.hand_landmarks[0][16].x - latest_result.hand_landmarks[0][4].x, latest_result.hand_landmarks[0][16].y - latest_result.hand_landmarks[0][4].y)
                pinch_ratio_index = pinch_gap_index / palm_area
                pinch_ratio_middle = pinch_gap_middle / palm_area
                pinch_ratio_ring = pinch_gap_ring / palm_area



                rawX= latest_result.hand_landmarks[0][9].x * screen_width
                rawY= latest_result.hand_landmarks[0][9].y * screen_height
                MappedX = int((rawX - (screen_width * framepercentw)) * (screen_width / (screen_width * (1 - 2 * framepercentw))))
                MappedY = int((rawY - (screen_height * framepercenth)) * (screen_height / (screen_height * (1 - 2 * framepercenth))))
                distance_to_target = math.hypot(SmoothX - MappedX, SmoothY - MappedY)
                if pinch_ratio_index < slowthreshold or pinch_ratio_middle < slowthreshold and not ispressed:
                    SmootheningFactor = 0.02
                else:
                    if distance_to_target < 15:
                        SmootheningFactor=0.05
                    else:
                        SmootheningFactor=0.30
                SmoothX = SmoothX + (MappedX - SmoothX) * SmootheningFactor
                SmoothY = SmoothY + (MappedY - SmoothY) * SmootheningFactor
                mouse.move(int(SmoothX), int(SmoothY), absolute=True, duration=0)

                if pinch_ratio_index < pressthreshold:
                    if not ispressed:
                        current_time = time.time()
                        if current_time - clicktime < 0.4:
                            mouse.double_click()
                            clicktime = 0
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

root.mainloop()

