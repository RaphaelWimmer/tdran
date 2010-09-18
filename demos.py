#!/usr/bin/python

import xk
from Xlib import XK
import cv   #using opencv 2.0 ctype python bindings
from utils import *
import pickle
from threading import *

class Record_keys:

    def __init__(self, params = None):
        self.keymap = {}
        self.record_key_finished = False # first wait for complete silence

    def process_touches(self, touches):
        if len(touches) == 0:
            self.record_key_finished = True
            return
        elif len(touches) > 1:
            print "multiple touches detected - touch only once!"
            return
        else: # => exactly one touch
            if self.record_key_finished == True: # => we want to assign a new touch
                self.record_key_finished = False
                pos = int(touches[0][Touch.POSITION])
                print "Waiting for key"
                key = cv.WaitKey(0)
                if key != 27: # Esc
                    self.keymap[pos] = key
    
    def shutdown(self):
        print self.keymap
        # save it
        pickle.dump(self.keymap, open("keymap.pickle","w"))

class Play_keys:
    
    Threshold = 5
    Autorepeat = False

    def __init__(self, params = None):
        if params:
            self.keymap = pickle.load(open(params))
        else:
            self.keymap = pickle.load(open("keymap.pickle"))

        self.Threshold = self.calc_min_distance(self.keymap) / 2
        print self.Threshold
        self.pressed_map_old = []

    def process_touches(self, touches):
       pressed_map_new = []
       for touch in touches:
           # TODO:  get key from keymap
           for keypos in self.keymap:
               if abs(touch[Touch.POSITION] - keypos) < self.Threshold :
                   pressed_map_new.append(self.keymap[keypos])
       if self.Autorepeat == True:
           for key in pressed_map_new:
                   print "type", key
                   xk.press_key(key)
                   xk.release_key(key)
       else: 
           for key in unique(pressed_map_new + self.pressed_map_old):
               if (key in pressed_map_new) and not (key in self.pressed_map_old):
                   print "press", key
                   xk.press_key(key)
               if (key in self.pressed_map_old) and not (key in pressed_map_new):
                   xk.release_key(key)
                   print "release", key
       self.pressed_map_old = pressed_map_new[:] # shallow copy
    
    def shutdown(self):
        pass

    def calc_min_distance(self, keymap):
        pos_a = sorted(keymap.keys())
        pos_b = pos_a[1:]
        return min(map(lambda x,y:abs(x-y), pos_b, pos_a[:-1]))

class Headphones:

    def __init__(self, params = None):
        cv.NamedWindow("Headphones", cv.CV_WINDOW_AUTOSIZE)
        self.headphone_images = {}
        for name in ["no_touch", "play", "prev", "next"]:
            self.headphone_images[name] = cv.LoadImage("headphones/" + name+".png")
        self.set_headphone("no_touch")

    def process_touches(self, touches):
        if len(touches) == 1:
            for touch in touches:
               if touch[Touch.PERCENTAGE] < 0.3:
                    print "Prev"
                    self.set_headphone("prev")
               elif touch[Touch.PERCENTAGE] < 0.6:
                    print "Toggle Play/Pause"
                    self.set_headphone("play")
               else:
                    print "Next"
                    self.set_headphone("next")
        elif len(touches) > 1:
            print "multiple touches"
        else:
            self.set_headphone("no_touch")
    
    def set_headphone(self, mode):
        cv.ShowImage("Headphones", self.headphone_images[mode])

    def shutdown(self):
        pass

class Piano2:

    def __init__(self, params = None):
       self.piano_map_old = []

    def process_touches(self, touches):
       piano_map_new = []
       for touch in touches:
           new_note = XK.XK_a + int(touch[Touch.PERCENTAGE] * (XK.XK_z - XK.XK_a))
           piano_map_new.append(new_note)

       for note in range(XK.XK_a, XK.XK_z):
           if (note in piano_map_new) and not (note in self.piano_map_old):
               print "press", note
               xk.press_key(note)
           if (note in self.piano_map_old) and not (note in piano_map_new):
               xk.release_key(note)
               print "release", note
       self.piano_map_old = piano_map_new[:] # shallow copy

    def shutdown(self):
        pass

class Piano:

    def __init__(self, params = None):
        import tone
        self.synth = tone.Synth(3)
        self.synth.start_synth()
        self.synth.clear()

    def process_touches(self, touches):
        if len(touches) > 0:
            for touch in range(len(touches)):
               tone = 440 + 440 * touches[touch][Touch.PERCENTAGE]
               self.synth.set(touch, tone)
        else:
            self.synth.clear()
    
    def shutdown(self):
        synth.stop_synth()


class Tcp:

    def __init__(self, params = ("127.0.0.1",2345)):
        self.server = TCP_Server(params)
        self.server.start()

    def process_touches(self, touches):
        if not self.server.connected:
            return
        else:
            for touch in touches:
                print "sending touch"
                self.server.send("touch,%d,%d\r\n" % (touch[Touch.POSITION],touch[Touch.AMPLITUDE]))

    def shutdown(self):
        self.server.stop()


class TCP_Server(Thread):
    
    def __init__(self, params = ("127.0.0.1",2345)):
        Thread.__init__(self)
        import socket
        import Queue
        import time
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(params)
        self.s.listen(1)
        self.conn = None
        self.queue = Queue.Queue()
        self.connected = False
    
    def run(self):
        self.running = True
        self.conn, addr = self.s.accept()
        print 'Connected by', addr
        self.connected = True
        while self.running:
            data = self.queue.get()
            self.conn.send(data)
            print "Sent data:", data
        self.conn.close()

    def stop(self):
        self.running = False

    def send(self, data):
        self.queue.put(data)
