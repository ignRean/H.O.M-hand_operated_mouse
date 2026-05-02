import cv2 as cv
import sys
image=cv.imread(cv.samples.findFile("starry_night.jpg"))
if image is None:
    sys.exit("Could not read the image.")

cv.imshow("Display window", image)
k = cv.waitKey(0)
if k == ord("s"):
    cv.imwrite("starry_night.png", image)