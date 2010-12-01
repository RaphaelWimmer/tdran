#!/usr/bin/python

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
    update_undistort_map()

def cb_fy(val):
    global fy
    fy = val
    update_undistort_map()

def cb_cx(val):
    global cx
    cx = val
    update_undistort_map()

def cb_cy(val):
    global cy
    cy = val
    update_undistort_map()

def cb_k1(val):
    global k1
    k1 = val
    update_undistort_map()

def cb_k2(val):
    global k2
    k2 = val
    update_undistort_map()

def cb_p1(val):
    global p1
    p1 = val
    update_undistort_map()

def cb_p2(val):
    global p2
    p2 = val
    update_undistort_map()


intrinsics = None
dist_coeffs = None
src = None
dst = None
mapx = None
mapy = None

def init_undistort(interactive = True):
    global intrinsics, dist_coeffs, src, dst, mapx, mapy
    global fx, fy, cx, cy, k1, k2, p1, p2
    intrinsics = cv.CreateMat(3, 3, cv.CV_64FC1)
    dist_coeffs = cv.CreateMat(1, 4, cv.CV_64FC1)
    dst = cv.CreateImage(cv.GetSize(src), src.depth, src.nChannels)
    mapx = cv.CreateImage(cv.GetSize(src), cv.IPL_DEPTH_32F, 1)
    mapy = cv.CreateImage(cv.GetSize(src), cv.IPL_DEPTH_32F, 1)

    if interactive:
        win = cv.NamedWindow("Settings", cv.CV_WINDOW_AUTOSIZE)
        cv.CreateTrackbar("fx", "Settings", fx, 3000, cb_fx)
        cv.CreateTrackbar("fy", "Settings", fy, 3000, cb_fy)
        cv.CreateTrackbar("cx", "Settings", cx, 640, cb_cx)
        cv.CreateTrackbar("cy", "Settings", cy, 480, cb_cy)
        cv.CreateTrackbar("k1", "Settings", k1, 1000, cb_k1)
        cv.CreateTrackbar("k2", "Settings", k2, 1000, cb_k2)
        cv.CreateTrackbar("p1", "Settings", p1, 1000, cb_p1)
        cv.CreateTrackbar("p2", "Settings", p2, 1000, cb_p2)

def update_undistort_map():
    global intrinsics, dist_coeffs, src, dst, mapx, mapy
    global fx, fy, cx, cy, k1, k2, p1, p2
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

def undistort(src):
    global intrinsics, dist_coeffs, src, dst, mapx, mapy
    global fx, fy, cx, cy, k1, k2, p1, p2
    cv.Remap(src, dst, mapx, mapy, cv.CV_INTER_LINEAR + cv.CV_WARP_FILL_OUTLIERS,  cv.ScalarAll(0))

    # cv.Undistort2(src, dst, intrinsics, dist_coeffs)
    return dst

