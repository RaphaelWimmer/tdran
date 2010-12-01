#!/usr/bin/python

# ./undistort 0_0000.jpg 1367.451167 1367.451167 0 0 -0.246065 0.193617 -0.002004 -0.002056

import sys
import cv
import time

fx = 620
fy = 1367
cx = 335
cy = 237
k1 = 0
k2 = 815
p1 = 500
p2 = 500

def cb_fx(val):
    global fx
    fx = val

def cb_fy(val):
    global fy
    fy = val

def cb_cx(val):
    global cx
    cx = val

def cb_cy(val):
    global cy
    cy = val

def cb_k1(val):
    global k1
    k1 = val

def cb_k2(val):
    global k2
    k2 = val

def cb_p1(val):
    global p1
    p1 = val

def cb_p2(val):
    global p2
    p2 = val

    
win = cv.NamedWindow("Undistort", cv.CV_WINDOW_AUTOSIZE)
win = cv.NamedWindow("Settings", cv.CV_WINDOW_AUTOSIZE)

cv.CreateTrackbar("fx", "Settings", fx, 3000, cb_fx)
cv.CreateTrackbar("fy", "Settings", fy, 3000, cb_fy)
cv.CreateTrackbar("cx", "Settings", cx, 640, cb_cx)
cv.CreateTrackbar("cy", "Settings", cy, 480, cb_cy)
cv.CreateTrackbar("k1", "Settings", k1, 1000, cb_k1)
cv.CreateTrackbar("k2", "Settings", k2, 1000, cb_k2)
cv.CreateTrackbar("p1", "Settings", p1, 1000, cb_p1)
cv.CreateTrackbar("p2", "Settings", p2, 1000, cb_p2)


if len(sys.argv) < 2:
    print 'Usage: %s input-file' % sys.argv[0]
    sys.exit(-1)

#cv.StartWindowThread()
src = sys.argv[1]
intrinsics = cv.CreateMat(3, 3, cv.CV_64FC1)

dist_coeffs = cv.CreateMat(1, 4, cv.CV_64FC1)

src = cv.LoadImage(src)
dst = cv.CreateImage(cv.GetSize(src), src.depth, src.nChannels)
mapx = cv.CreateImage(cv.GetSize(src), cv.IPL_DEPTH_32F, 1)
mapy = cv.CreateImage(cv.GetSize(src), cv.IPL_DEPTH_32F, 1)

running = True
while running:
    key = cv.WaitKey(7)
    #time.sleep(0.01)
    cv.Zero(intrinsics)
    intrinsics[0, 0] = float(fx)
    intrinsics[1, 1] = float(fy)
    intrinsics[2, 2] = 1.0
    intrinsics[0, 2] = float(cx)
    intrinsics[1, 2] = float(cy)
    cv.Zero(dist_coeffs)
    dist_coeffs[0, 0] = float(k1 -500) / 500.0
    dist_coeffs[0, 1] = float(k2 -500) / 500.0
    dist_coeffs[0, 2] = float(p1 -500) / 500.0
    dist_coeffs[0, 3] = float(p2 -500) / 500.0
    cv.InitUndistortMap(intrinsics, dist_coeffs, mapx, mapy)
    cv.Remap(src, dst, mapx, mapy, cv.CV_INTER_LINEAR + cv.CV_WARP_FILL_OUTLIERS,  cv.ScalarAll(0))
    # cv.Undistort2(src, dst, intrinsics, dist_coeffs)
    for y in range(48):
        cv.Line(dst,(0,y*10),(640,y*10),(255,0,0))

    cv.ShowImage("Undistort", dst)

