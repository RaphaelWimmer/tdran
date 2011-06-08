#!/usr/bin/python

import os
import time
import xk
from Xlib import XK
from pymouse import PyMouse
import cv   #using opencv 2.0 ctype python bindings
from utils import *
import pickle
from threading import *

class Record_keys:

    def __init__(self, params = None):
        self.keymap = {}
        self.record_key_finished = False # first wait for complete silence
        self.record_img = cv.LoadImage("record_keys/record.png")
        self.wait_img = cv.LoadImage("record_keys/wait.png")
        cv.NamedWindow("Record", cv.CV_WINDOW_AUTOSIZE)

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
                cv.ShowImage("Record", self.record_img)
                key = cv.WaitKey(0)
                if key != 27: # Esc
                    self.keymap[pos] = key
                cv.ShowImage("Record", self.wait_img)
    
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
           min_dist = 9999
           nearest_keypos = 9999
           for keypos in self.keymap:
               dist = abs(touch[Touch.POSITION] - keypos) 
               if dist < min_dist:
                   nearest_keypos = keypos
                   min_dist = dist
           pressed_map_new.append(self.keymap[nearest_keypos])
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

class Scroll_wheel:
    
    Autorepeat = False

    def __init__(self, params = None):
        self.old_pos = -1.0
        self.new_pos = -1.0
#        self.mouse = PyMouse()

    def process_touches(self, touches):
        if len(touches) == 0:
            self.old_pos = -1.0
            self.new_pos = -1.0
        else:
            self.new_pos = touches[0][Touch.PERCENTAGE]
            if self.old_pos != -1:
                moved = self.new_pos - self.old_pos
                if abs(moved) > 0.01: # arbitrary threshold
                    if moved > 0.0:
                        print "UP"
 #                       self.mouse.click(1,1,4)
                        xk.press_button(4)
                    else:
                        print "DOWN"
                        xk.press_button(5)
                    self.old_pos = self.new_pos
            else:
                self.old_pos = self.new_pos
    
    def shutdown(self):
        pass


class Headphones:

    def __init__(self, params = None):
        cv.NamedWindow("Headphones", cv.CV_WINDOW_AUTOSIZE)
        self.headphone_images = {}
        for name in ["no_touch", "play", "pause", "stop", "playing", "stopped"]:
            self.headphone_images[name] = cv.LoadImage("headphones/" + name+".png")
        self.volume = 30
        self.playing = False
        self.play_released = False
        self.set_headphone("no_touch")

    def process_touches(self, touches):
        if len(touches) == 1:
            for touch in touches:
               if touch[Touch.PERCENTAGE] > 0.8:
                    print "Toggle Play/Pause"
                    self.set_headphone("play")
               else:
                    print "Volume", touch[Touch.PERCENTAGE] / 0.8
                    self.volume = 100 - int(100.0 * touch[Touch.PERCENTAGE] * 1.25)
                    os.spawnlp(os.P_NOWAIT, "amixer", "amixer", "sset", "Master", "%d" % (self.volume))
                    if self.playing:
                        self.set_headphone("playing")
                    else:
                        self.set_headphone("stopped")
        elif len(touches) > 1:
            print "multiple touches"
        else:
            if self.playing:
                self.set_headphone("playing")
            else:
                self.set_headphone("stopped")
    
    def set_headphone(self, mode):
        if mode == "play" :
            if self.play_released:
                if self.playing:
                    os.popen("killall mplayer")
                    self.playing = False
                    self.play_released = False
                    mode = "pause"
                else: # paused
                    os.spawnlp(os.P_NOWAIT, "amixer", "amixer", "sset", "Master", "100")
                    os.spawnlp(os.P_NOWAIT, "playsound", "playsound", "headphones/play.wav")
                    os.spawnlp(os.P_NOWAIT, "amixer", "amixer", "sset", "Master", "30")
                    self.volume = 30
                    os.spawnlp(os.P_NOWAIT, "mplayer", "mplayer", "headphones/xylophone.mp3")
                    self.playing = True
                    self.play_released = False
        else:
            self.play_released = True

        cv.Rectangle(self.headphone_images[mode],(0,800), (1440,850), (255,255,255), cv.CV_FILLED)
        cv.Rectangle(self.headphone_images[mode],(0,805), (1440 * self.volume / 100 ,845), (0,0,0), cv.CV_FILLED)
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

    def __init__(self, params = ("",2345)):
        self.params = params
        self.server = TCP_Server(self.params)
        self.server.start()
        self.old_touch = 0
        self.start_touch_pos = 0
        self.threshold = 0 
        self.touch_average = 20
        self.touch_history = []

    def transmit(self, data):
        sent = self.server.send(data)
        if sent == False:
            self.server.stop()
            print "Connection interrupted"
            self.server = TCP_Server(self.params)
            self.server.start()

    def process_touches(self, touches):
        if not self.server.connected:
            return
        else:
            if len(touches) == 0 and self.old_touch != 0:
                self.transmit("release,0,%d,%d\r\n" % (self.old_touch,0))
                self.old_touch = 0 # FIXME: need to compensate tracking blackouts
                self.start_touch_pos = 0
                self.touch_history = []
            if len(touches) == 1:
                if self.old_touch == 0: # new touch
                    self.transmit("touch,0,%d,%d\r\n" % (touches[0][Touch.POSITION],
                                                          touches[0][Touch.AMPLITUDE]))
                    self.old_touch = touches[0][Touch.POSITION]
                    self.start_touch_pos = self.old_touch

                else: # move
                    # delta = touches[0][Touch.POSITION] - self.old_touch
                    delta = touches[0][Touch.POSITION] - self.start_touch_pos
                    self.touch_history.append(delta)
                    if len(self.touch_history) > self.touch_average:
                        self.touch_history.pop(0)
                    delta = sum(self.touch_history) / len(self.touch_history)
                    if abs(delta) > self.threshold:
                        bytes_sent = self.transmit("move,0,%d,%d\r\n" % (delta, touches[0][Touch.AMPLITUDE]))
                    self.old_touch = touches[0][Touch.POSITION]

            else: # multiple touches
                for touch in touches:
                    print "sending raw touch"
                    bytes_sent = self.transmit("raw_touch,%d,%d\r\n" % (touch[Touch.POSITION],touch[Touch.AMPLITUDE]))

    def shutdown(self):
        if self.server.running:
            self.server.stop()
        else: # server is waiting for connection
            self.server.s.close()

class TCP_Server(Thread):
    
    def __init__(self, params = ("",2345)):
        Thread.__init__(self)
        import socket
        import Queue
        import time
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(params)
        self.s.listen(1)
        self.conn = None
        self.queue = Queue.Queue()
        self.running = False
        self.connected = False
    
    def run(self):
        self.conn, addr = self.s.accept()
        self.running = True
        print 'Connected by', addr
        self.connected = True
        self.conn.send("Hello,0,0,0\r\n")
        while self.running:
            data = self.queue.get()
            try:
                self.conn.send(data)
            except:
                print "Connection broken"
                self.running = False
            print "Sent data:", data
        self.conn.close()

    def stop(self):
        self.running = False

    def send(self, data):
        if self.running:
            self.queue.put(data)
            return True
        else:
            return False

class Identification:
    

    def __init__(self, params = None):
        if params:
            self.ids = pickle.load(open(params))
        else:
            try:
                self.ids = pickle.load(open("ids.pickle"))
            except:        
                self.ids = {}
                
        self.THRESHOLD = 10 # pixels 
        self.old_id = 0
        self.no_img = cv.LoadImage("identification/id_no_output.png")
        self.earphones_img = cv.LoadImage("identification/id_earphones.png")
        self.headphones_img = cv.LoadImage("identification/id_headphones.png")
        self.loudspeaker_img = cv.LoadImage("identification/id_loudspeaker.png")
        self.images = [self.no_img,
                       self.headphones_img,
                       self.earphones_img,
                       self.loudspeaker_img ]
        cv.NamedWindow("Identify", cv.CV_WINDOW_AUTOSIZE)
        cv.ShowImage("Identify", self.images[0])

    def process_touches(self, touches):
        #if len(touches) == 0 or len(touches) > 3:
        #    return
        #else: 
            pat_id = self.match_pattern(touches) 
            # check if pattern has been recorded before
            if pat_id == None:
                pat_id = 0 # show id_no_output.png
            if pat_id != self.old_id:
                print "Found Pattern:", pat_id
                cv.ShowImage("Identify", self.images[pat_id])
            self.old_id = pat_id
                
    
    def shutdown(self):
        pass

    def match_pattern(self, touches):
        pattern = self.to_pattern(touches)
        for pat_id in self.ids.keys():
            pat = self.ids[pat_id]
            match = 1
            for i in range(min(len(pattern),len(pat))):
                if abs(pattern[i] - pat[i]) > self.THRESHOLD:
                    match = 0
                    break
            if match == 1 and len(pattern) == len(pat):
                return pat_id
        return None

    def to_pattern(self, touches):
        pattern = []
        for touch in touches:
            pattern.append(touch[Touch.POSITION])
        return pattern

class Recordidentification:

    def __init__(self, params = None):
        if params:
            self.ids = pickle.load(open(params))
        else:
            try:
                self.ids = pickle.load(open("ids.pickle"))
            except:        
                self.ids = {}
                
        self.THRESHOLD = 10 # pixels 
        self.record_img = cv.LoadImage("record_keys/record.png")
        self.wait_img = cv.LoadImage("record_keys/wait.png")
        cv.NamedWindow("Record", cv.CV_WINDOW_AUTOSIZE)

    def process_touches(self, touches):
        if len(touches) == 0 or len(touches) > 3:
            return
        else: 
            pat_id = self.match_pattern(touches) 
            # check if pattern has been recorded before
            if pat_id == None:
                # no - record it.
                pos = int(touches[0][Touch.POSITION])
                print "Waiting for key"
                cv.ShowImage("Record", self.record_img)
                key = cv.WaitKey(0)
                if key != 27: # Esc
                    self.add_id(touches, int(chr(key)))
                cv.ShowImage("Record", self.wait_img)
            else:
                print "Pattern:", pat_id
    
    def shutdown(self):
        print self.ids
        # save it
        pickle.dump(self.ids, open("ids.pickle","w"))

    def match_pattern(self, touches):
        pattern = self.to_pattern(touches)
        for pat_id in self.ids.keys():
            pat = self.ids[pat_id]
            match = 1
            for i in range(min(len(pattern),len(pat))):
                if abs(pattern[i] - pat[i]) > self.THRESHOLD:
                    match = 0
                    break
            if match == 1 and len(pattern) == len(pat):
                return pat_id
        return None

    def add_id(self, touches, pat_id):
        pattern = self.to_pattern(touches)
        self.ids[pat_id] = self.to_pattern(touches)

    def to_pattern(self, touches):
        pattern = []
        for touch in touches:
            pattern.append(touch[Touch.POSITION])
        return pattern

class Slider:

    def __init__(self, params = None):
        cv.NamedWindow("Slider", cv.CV_WINDOW_AUTOSIZE)
        self.value = 0
        self.started = False
        self.completed = False
        self.img_slider = cv.LoadImage("slider/slider_bg.png")
        cv.Rectangle(self.img_slider,(0,250), (800,350), (255,255,255), cv.CV_FILLED)
        cv.ShowImage("Slider", self.img_slider)

    def process_touches(self, touches):
        if len(touches) == 1:
            for touch in touches:
                self.value = touch[Touch.PERCENTAGE]
                cv.Rectangle(self.img_slider,(0,250), (800,350), (255,255,255), cv.CV_FILLED)
                cv.Rectangle(self.img_slider,(5,255), (790 * self.value + 5 ,345), (0,0,0), cv.CV_FILLED)
                cv.ShowImage("Slider", self.img_slider)
        elif len(touches) > 1:
            print "multiple touches"

    def shutdown(self):
        pass

class Bar:

    def __init__(self, params = None):
        cv.NamedWindow("Bar", cv.CV_WINDOW_AUTOSIZE)
        self.value = 0
        self.width = 20
        self.height = 100
        self.started = False
        self.completed = False
        self.img_slider = cv.LoadImage("slider/slider_bg.png")
        cv.ShowImage("Bar", self.img_slider)

    def process_touches(self, touches):
        if len(touches) == 1:
            for touch in touches:
                self.value = touch[Touch.PERCENTAGE]
                cv.Rectangle(self.img_slider,(0,0), (800,600), (0,0,0), cv.CV_FILLED)
                cv.Rectangle(self.img_slider,(800 * self.value - self.width/2, (600 - self.height) /2), (800 * self.value + self.width/2, (600 + self.height) /2), (255,255,255), cv.CV_FILLED)
                cv.ShowImage("Bar", self.img_slider)
        elif len(touches) > 1:
            print "multiple touches"

    def shutdown(self):
        pass

class Slidergame:

    def __init__(self, params = None):
        cv.NamedWindow("Slider", cv.CV_WINDOW_AUTOSIZE)
        self.value = 0
        self.started = False
        self.completed = False
        self.img_slider = cv.LoadImage("slider/slider_bg.png")
        self.img_complete = cv.LoadImage("slider/slider_complete.png")
        self.img_failed = cv.LoadImage("slider/slider_failed.png")
        cv.Rectangle(self.img_slider,(0,250), (800,350), (255,255,255), cv.CV_FILLED)
        cv.ShowImage("Slider", self.img_slider)

    def process_touches(self, touches):
        if len(touches) >= 1:
            self.value = touches[0][Touch.PERCENTAGE]
            if (not self.started) and self.value < 0.10: # begin new game
                self.started = True
                self.completed = False
            if self.started:
                cv.Rectangle(self.img_slider,(0,250), (800,350), (255,255,255), cv.CV_FILLED)
                cv.Rectangle(self.img_slider,(5,255), (790 * self.value + 5 ,345), (0,0,0), cv.CV_FILLED)
                cv.ShowImage("Slider", self.img_slider)
                if self.value > 0.85:
                    self.completed = True
                    self.started = False
                    cv.ShowImage("Slider", self.img_complete)
        elif self.started:
            if self.value > 0.90:
                self.completed = True
                self.started = False
                cv.ShowImage("Slider", self.img_complete)
            else:
                self.completed = True
                self.started = False
                cv.ShowImage("Slider", self.img_failed)

    def shutdown(self):
        pass

class Grasp:

    def __init__(self, params = None):
        cv.NamedWindow("Grasp", cv.CV_WINDOW_AUTOSIZE)
        cv.NamedWindow("Grasp Settings", cv.CV_WINDOW_AUTOSIZE)
        self.top_right = 45
        self.top_left = 60
        self.left = 333
        self.right = 570
        self.top = 562
        cv.CreateTrackbar("Top Right", "Grasp Settings", self.top_right, 100, self.change_top_right)
        cv.CreateTrackbar("Top Left", "Grasp Settings", self.top_left, 100, self.change_top_left)

        self.img_bg = cv.LoadImage("grasp/siemens_cxt70.jpg")
        self.img = cv.LoadImage("grasp/siemens_cxt70.jpg")
        
        cv.ShowImage("Grasp", self.img)

    def change_top_right(self, val):
        self.top_right = val

    def change_top_left(self, val):
        self.top_left = val

    def process_touches(self, touches):
        self.img = cv.CloneImage(self.img_bg)
        for touch in touches:
            val = abs(int(touch[Touch.AMPLITUDE]))
            if touch[Touch.PERCENTAGE] * 100 < self.top_right:
                pos = int((touch[Touch.PERCENTAGE] * 100 / self.top_right) * self.top)
                width = self.top / (len(touches) * self.top_right / 100.0)
                cv.Rectangle(self.img, (self.right, self.img.height - (pos - width/2)), (self.right + val, self.img.height - (pos + width/2)), (255,125,125), cv.CV_FILLED)
            elif touch[Touch.PERCENTAGE] * 100 <= self.top_left:
                pos = int((touch[Touch.PERCENTAGE] * 100 - self.top_right) / (self.top_left - self.top_right) * (self.right - self.left))
                width = (self.right - self.left) / (len(touches) * (self.top_left - self.top_right) / 100.0)
                cv.Rectangle(self.img, (self.right - (pos - width/2), self.img.height - self.top), (self.right - (pos + width/2), self.img.height - (self.top + val)), (255,125,255), cv.CV_FILLED)
            else: # > self.top_left
                pos = int((touch[Touch.PERCENTAGE] * 100 - self.top_left) / (100 - self.top_left) * self.top)
                width = self.top / (len(touches) * (100 - self.top_left) / 100.0)
                cv.Rectangle(self.img, (self.left, self.img.height - self.top + pos - width/2), (self.left - val, self.img.height - self.top + (pos + width/2)), (125,255,125), cv.CV_FILLED)

        cv.ShowImage("Grasp", self.img)

    def shutdown(self):
        pass
