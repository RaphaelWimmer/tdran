#!/usr/bin/python

import cv	#using opencv 2.0 ctype python bindings
from numpy import *
from scipy import interpolate, misc, fftpack, signal

import datetime
import os
import tone

import sys
from PyQt4 import QtGui

def discreteDerivative(trace):
	return trace - roll(trace,1,0)

def filterMovingAverage(trace, size):
	filtered = list(trace)
	for i in range (size, 640-size):
		filtered[i] = 0
		for j in range(-size, size+1):
			filtered[i] = filtered[i] + trace[i+j]
		filtered[i] /= size*2+1
	return filtered

def drawGrid(image):
	pts = []
	#vertical
	for i in range(0,640,64):
		pts.append([(i,0), (i,480)])
	#horizontal
	for i in range(48,480,64):
		pts.append([(0,i), (640,i)])
	cv.PolyLine(image, pts, 0, (50,50,50))
	#baseline
	cv.Line(imageColor, (display[0],240), (display[1],240), (255,255,255))
	#range
	cv.Line(imageColor, (display[0],0), (display[0],480), (0,255,0))
	cv.Line(imageColor, (display[1],0), (display[1],480), (0,0,255))
	#threshold
	cv.Line(imageColor, (0,240+threshold[0]), (640,240+threshold[0]), (128,128,128))

def analyzeImage(image, mask):
	trace = []
	xv = []
	#analyze trace
	for x in range(0,640):
		column = cv.GetCol(image, x)
		(minVal,maxVal,minLoc,(maxLocX,maxLocY)) = cv.MinMaxLoc(column)
		if maxVal > 100 and maxLocY > 1:
			if not ((x,maxLocY) in mask):
				trace.append(maxLocY)
				xv.append(x)
	return array(xv), array(trace)

def printTrace(trace, image, color, visible, shift=0, scale=1):
	pts=[]
	first,last=visible
	for x in range(first,last):
		pts.append((x,int(((trace[x]*scale)+shift))));
	cv.PolyLine(image,[pts], 0, color)

def on_mouse(event, x, y, flags, param):
	if event == cv.CV_EVENT_LBUTTONDOWN:
		display[0] = x
	if flags & cv.CV_EVENT_FLAG_LBUTTON > 0:
		if x > display[0]: display[1] = x
	if event == cv.CV_EVENT_LBUTTONUP:
		if x > display[0]: display[1] = x
	if event == cv.CV_EVENT_RBUTTONDOWN:
		threshold[0] = y - 240
		print "threshold" + str(threshold)

def sinc(i,f):
	return sin(2*math.pi*f*i)/i*math.pi

def kernel(i):
	return ones(i) / i

def autorange(calibrated):
	first = 0
	last = 640
	for i in range(0,640):
		#find first silence
		if calibrated[i] > threshold[0] / 5:
			first = i
		if i > first + 100:
			break
	first = first + 10
	for i in range(first,640):
		#find last silence
		if calibrated[i] > threshold[0] / 5:
			last = i
			break
	last = last - 10
	display[0] = first
	display[1] = last 

#GUI
window = cv.NamedWindow("TDR", cv.CV_WINDOW_AUTOSIZE)
cv.SetMouseCallback("TDR", on_mouse,0)

app = QtGui.QApplication(sys.argv)

#Capturing
cap = cv.CaptureFromCAM(0)
cv.SetCaptureProperty(cap, cv.CV_CAP_PROP_FPS, 30)

#Imaging
imageColor = cv.CreateImage([640,480], cv.IPL_DEPTH_8U, 3)

#Global
display=[0,639]
threshold = [30]
shot = 0
pause = 0
grid = 1
traces = 0
detection = 0
pixelmask = [(98, 187), (106, 240), (120, 425), (133, 238), (519, 199)]
detected = []
markers = []

topicName = ""

calibrationTimer = 0
history = zeros([25,640])
calibrated = zeros(640)
calibration = zeros(640)

corrSample = zeros(50)
sc = abs(sinc(arange(0-320,640-210),0.03))

synth = tone.Synth(3)
synth.start()

play_sound = False

while True:
	#CAPTURE
	img = cv.QueryFrame(cap)
	
	if pause == 0:
		cv.CvtColor(img, imageColor, cv.CV_GRAY2RGB)
		
		#GRID
		if grid != 0: drawGrid(imageColor)
		
		#ANALYZE
		x,trace = analyzeImage(img, pixelmask)
		if x.size < 2:
			x = array([0,640])
			trace = zeros(2)
		f = interpolate.interp1d(x, trace, bounds_error = 0, fill_value = 0)
			
		
		xa = arange(0,640) 
		interpolated = f(xa)
		
		#moving average
		avg =signal.fftconvolve(interpolated, kernel(5), mode='same')
		
		#time average
		history = roll(history, -1, 0)
		history[-1] = interpolated

		alterationSpeed = abs(history[-1] - history[-2])
		alterationSpeed = signal.fftconvolve(alterationSpeed, ones(30)/30, mode='same')
		
		maskAlteration = where(alterationSpeed > threshold[0] / 3, 1, 0)
		maskStatic = where(maskAlteration, 0, 1)
		
		maskAlteration = signal.fftconvolve(maskAlteration, kernel(15), mode='same')
		maskStatic = signal.fftconvolve(maskStatic, kernel(15), mode='same')

		history = history * maskStatic + avg*maskAlteration
		
		filtered = average(history,0)
		
		
		#derivative = misc.derivative(f, xa)
		#derivative = signal.fftconvolve(discreteDerivative(filtered), mav3kernel, mode='same')
		
		#CALIBRATION
		calibrated = filtered - calibration
		
		#derivative
		derivative = signal.fftconvolve(discreteDerivative(calibrated)*10, kernel(10), mode='same')
			
		#correlate
		#correlation = signal.correlate(calibrated, corrSample, mode='same')
			
		#FIND FINGER PRESS
		if detection == 1:
			detected = []
			for i in range(display[0], display[1]):
				if ((calibrated[i] > threshold[0]) and ((derivative[i] > 0 and derivative[i+1] <= 0))): #or (derivative[i] >= 0 and derivative[i+1] < 0)
					cv.Line(imageColor, (i,0), (i,480), (255,255,255))
					detected.append(i)
					#os.system('beep -f 200 -l 0.1')
		
		#PRINT TRACES
		if traces == 1:
			printTrace(interpolated, imageColor, (0,0,255), display)
			printTrace(calibrated, imageColor, (0,255,0), display, shift=240)
			printTrace(derivative, imageColor, (0,0,255), display, shift=240)
			#printTrace(alterationSpeed, imageColor, (255,0,0), display, shift=300)
			#printTrace(maskAlteration, imageColor, (255,0,0), display, shift=300, scale=100)
			#printTrace(sc, imageColor, (255,0,0), display, shift=240, scale=300)
		
		for i in markers:
			cv.Line(imageColor, (i,0), (i,480), (75,75,150))
		#SHOW
		cv.ShowImage("TDR",imageColor)

        if play_sound == True:
            # play sound: 
            if len(detected) > 0:
                for touch in range(len(detected)):
                   percentage = float(detected[touch] - display[0]) / float(display[1] - display[0])
                   tone = 440 + 440 * percentage
                   synth.set(touch, tone)
            else:
                synth.clear()
		
	#autoCalibrate
	calibrationTimer += 1
	if calibrationTimer == 30:
		calibration = array(filtered)

	if calibrationTimer == 31:
		autorange(calibrated)
		traces = 1
		detection = 1
		
	#SIGNALS
	key = cv.WaitKey(7)
	key &= 1048575
	if key == 27:	#esc
		break
	if key == ord('c'):	#c
		print "Calibrating..."
		calibration = array(filtered)
		detection = 1
	if key == ord('a'):
		print "Autorange"
		calibration = array(filtered)
		autorange(calibrated)
	if key == ord('m'):
		print "Mask dead pixels"
		for i in range(x.size):
			pt = (x[i], trace[i])
			if not pt in pixelmask:
				pixelmask.append(pt)
		print pixelmask
	if key == ord('f'):
		corrSample = calibrated[display[0]:display[1]]
		print "Catched signal for correlation."
		print corrSample
#	if key == ord('n'):
#		tn, ok = QtGui.QInputDialog.getText(None, "Name fuer Screenshots", "Thema")
#		if ok:
#			topicName = str(tn)
#		print "Naming images: " + topicName
	if key == ord(','):
		markers.extend(detected)
		print "Added to markers."
	if key == ord('.'):
		markers = []
		print "New markers."
	if key == ord('t'):
		if traces == 1: traces = 0
		else: traces = 1
		print "Traces: " + str(traces)
	if key == 1048679 or key == 103:	#g
		if grid == 1: grid = 0
		else:	grid = 1
		print "Display grid: " + str(grid)
	if key == 1048676 or key == 100:	#d
		if detection == 1: detection = 0
		else: detection = 1
		print "Detection: " + str(detection)
	if key == 1048608 or key == 32:	#space
		if pause == 1: pause = 0
		else: pause = 1
		print "Pause: " + str(pause)
	if key == 9:		#tab
		#if topicName == "": 
		tn, ok = QtGui.QInputDialog.getText(None, "Name fuer Screenshots", "Thema")
		if ok:
			topicName = str(tn)
		dt = datetime.datetime.now()
		if not os.path.exists("shots/" + dt.strftime("%Y-%m-%d")):
			os.mkdir("shots/" + dt.strftime("%Y-%m-%d"))
		shot += 1
		filename = "shots/" + dt.strftime("%Y-%m-%d") + "/" + dt.strftime("%Y-%m-%d %H:%M:%S") + " Shot "+str(shot)+" ("+topicName+").png"
		print "Saving image: '" + filename + "'"
		cv.SaveImage(filename, imageColor)

#Release & Destroy
cv.DestroyAllWindows()
