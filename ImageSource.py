#!/usr/bin/env python

import cv
import re

class ImageSource:
    def __init__(self, start_file="img/0000000000.png"):
        m = re.search("(^.*\D)(\d+)(\..*)", start_file)
        self.prefix = m.group(1)
        self.frame_no = int(m.group(2))
        self.start_frame_no = self.frame_no
        self.digits = len(m.group(2))
        self.template_string = "%0" + str(self.digits) + "d"
        self.extension = m.group(3)
        self.imgGray = cv.CreateImage([640,480], cv.IPL_DEPTH_8U, 1)

    def current(self):
        return self.imgGray
        
    def next(self):
        self.frame_no += 1
        filename = self.prefix + (self.template_string % self.frame_no) + self.extension
        try:
            self.img = cv.LoadImage(filename)
        except:
            self.img = None
        if not self.img:
            self.frame_no = self.start_frame_no
            filename = self.prefix + (self.template_string % self.frame_no) + self.extension
            self.img = cv.LoadImage(filename)
        cv.CvtColor(self.img, self.imgGray, cv.CV_RGB2GRAY)
        return self.imgGray
       
    def previous(self):
        self.frame_no -= 1
        filename = self.prefix + (self.template_string % self.frame_no) + self.extension
        try:
            self.img = cv.LoadImage(filename)
        except:
            self.img = None
        if not self.img:
            self.frame_no = self.start_frame_no
            filename = self.prefix + (self.template_string % self.frame_no) + self.extension
            self.img = cv.LoadImage(filename)
        cv.CvtColor(self.img, self.imgGray, cv.CV_RGB2GRAY)
        return self.imgGray

