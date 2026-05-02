import numpy as np
import cv2 as cv

cap = cv.VideoCapture(0)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 720)
if not cap.isOpened():
    print("Cannot open camera")
    exit()
while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    flipped_frame = (cv.flip(frame,1))
    rgbFrame = cv.cvtColor(flipped_frame, cv.COLOR_BGR2RGB)
    CorrectFlippedFrame = cv.cvtColor(rgbFrame, cv.COLOR_RGB2BGR)
    cv.imshow('frame', CorrectFlippedFrame)
    if cv.waitKey(1) == ord('q'):
        break
cap.release()
cv.destroyAllWindows()