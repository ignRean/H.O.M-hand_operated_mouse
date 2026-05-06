import cv2 as cv

print("Searching for active cameras...")

# Checks indices 0 through 4
for i in range(5):
    cap = cv.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✅ SUCCESS: Camera found at index {i}")
            cv.imshow(f"Is this DroidCam? (Index {i})", frame)
            cv.waitKey(3000) # Displays the camera for 3 seconds
            cv.destroyAllWindows()
        cap.release()
    else:
        print(f"❌ Failed: No camera at index {i}")
        
print("Search complete.")