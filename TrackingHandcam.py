import cv2 as cv #OpenCV is used for the Live webcam feed.
import mediapipe as mp #this is used for hand tracking
import time #This is for calculating the FPS of the hand tracking to see how well it performs on my computer.
import mouse #This is the main library i will be using to control the mouse.
import ctypes # i ma use this to get the screen resolution to better map the hand to mouse.
import math #this is used to calculate the distance between the thumb and index finger to determine when to click.


#Ts was slightly hard to understand but i got it cuz i am him
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

#intilize all the globle variables here. 
latest_result = None
last_print_time = 0
user32=ctypes.windll.user32
screen_width, screen_height = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
SmoothX, SmoothY = 0, 0
SmootheningFactor = 0.15
framepercentw = 0.35
framepercenth = 0.35
ispressed = False
frezzethreshold = 0.10
pressthreshold = 0.06
#pressthresholdrightclick = 0.015
#releasethreshold = 0.10

def print_result(result: HandLandmarker, output_image: mp.Image, timestamp_ms: int):
    global latest_result
    latest_result = result

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='hand_landmarker.task'),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=print_result,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.2,
    min_tracking_confidence=0.2,
    num_hands=1 # Allows tracking both hands
)

FINGER_MAP = {
    "THUMB":  ([(1,2), (2,3), (3,4)], (255, 0, 0)),     # Blue
    "INDEX":  ([(5,6), (6,7), (7,8)], (0, 255, 0)),     # Green
    "MIDDLE": ([(9,10), (10,11), (11,12)], (0, 0, 255)), # Red
    "RING":   ([(13,14), (14,15), (15,16)], (0, 255, 255)), # Yellow
    "PINKY":  ([(17,18), (18,19), (19,20)], (255, 0, 255)), # Magenta
    "PALM":   ([(0,1), (0,5), (9,13), (13,17), (5,9), (0,17)], (255, 255, 255)) # White
}

with HandLandmarker.create_from_options(options) as landmarker:
    cap = cv.VideoCapture(0)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 720) 
    frame_timestamp_ms = 0
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success: break
        
        frame = cv.flip(frame, 1)
        h, w, _ = frame.shape
        frame_small = cv.resize(frame, (w // 2, h // 2))
        rgb_frame = cv.cvtColor(frame_small, cv.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        frame_timestamp_ms += 1
        landmarker.detect_async(mp_image, frame_timestamp_ms)
        if latest_result and latest_result.hand_landmarks:
            for hand_lms in latest_result.hand_landmarks:
                # Draw Connections
                for name, (connections, color) in FINGER_MAP.items():
                   for connection in connections:
      
                        p1 = hand_lms[connection[0]]
                        p2 = hand_lms[connection[1]]

                        start = (int(p1.x * w), int(p1.y * h))
                        end = (int(p2.x * w), int(p2.y * h))
                        cv.line(frame, start, end, color, 3)
                for lm in hand_lms:
                        cv.circle(frame, (int(lm.x * w), int(lm.y * h)), 4, (255, 255, 255), -1)
            pinch_gap_index= math.hypot(latest_result.hand_landmarks[0][8].x - latest_result.hand_landmarks[0][4].x, latest_result.hand_landmarks[0][8].y - latest_result.hand_landmarks[0][4].y)
            pinch_gap_middle= math.hypot(latest_result.hand_landmarks[0][12].x - latest_result.hand_landmarks[0][4].x, latest_result.hand_landmarks[0][12].y - latest_result.hand_landmarks[0][4].y)
            pinch_gap_ring= math.hypot(latest_result.hand_landmarks[0][16].x - latest_result.hand_landmarks[0][4].x, latest_result.hand_landmarks[0][16].y - latest_result.hand_landmarks[0][4].y)
            if pinch_gap_index < frezzethreshold:
                pass
            elif pinch_gap_middle < frezzethreshold:
                pass
            else:
                rawX= latest_result.hand_landmarks[0][8].x * screen_width
                rawY= latest_result.hand_landmarks[0][8].y * screen_height
                MappedX = int((rawX - (screen_width * framepercentw)) * (screen_width / (screen_width * (1 - 2 * framepercentw))))
                MappedY = int((rawY - (screen_height * framepercenth)) * (screen_height / (screen_height * (1 - 2 * framepercenth))))
                SmoothX = SmoothX + (MappedX - SmoothX) * SmootheningFactor
                SmoothY = SmoothY + (MappedY - SmoothY) * SmootheningFactor
                mouse.move(SmoothX, SmoothY, absolute=True, duration=0)

            if pinch_gap_index < pressthreshold:
                if not ispressed:
                    mouse.click() 
                    ispressed = True
                    print("clicked")
            elif pinch_gap_middle < pressthreshold:
                if not ispressed:
                    mouse.right_click()
                    ispressed = True
                    print("Right Clicked")
                    print(pinch_gap_middle)
            elif pinch_gap_ring < pressthreshold:
                if not ispressed:
                    mouse.press()
            elif pinch_gap_ring > pressthreshold:
                if ispressed:
                    mouse.release()
                    ispressed = False
                    print("Released")

                

            else:
                ispressed = False


        cv.imshow('Custom Color Coded Tracker', frame_small)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv.destroyAllWindows()


