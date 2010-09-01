#!/usr/bin/python

from pyeca import *

class Synth:
    def __init__(self, channels=1):
        self.channels = channels
        self.e = ECA_CONTROL_INTERFACE(0)
        self.e.command("cs-add play_chainsetup")
        selected=""
        for i in range(channels):
           self.e.command("c-add sin"+str(i))
           self.e.command("c-select sin"+str(i))
           self.e.command("ai-add null")
           self.e.command("cop-add el:sine_fcac,440,1")
        
        self.e.command("c-select-all")
        self.e.command("ao-add /dev/dsp")
        self.e.command("cs-connect")
        #print self.e.command("c-status")

    def start(self):
        self.e.command("start")
    
    def stop(self):
        self.e.command("stop")

    def set(self, channel, freq):
        self.e.command("c-select sin"+str(channel))
        self.e.command("cop-select 2")
        self.e.command("copp-select 1")
        self.e.command("copp-set " + str(freq))

    def clear(self):
        for i in range(self.channels):
            self.e.command("c-select sin"+str(i))
            self.e.command("cop-select 2")
            self.e.command("copp-select 1")
            self.e.command("copp-set " + str(0))
        


if __name__ == "__main__":
    import time
    import sys
    s = Synth(4)
    s.start()
    s.set(0,440)
    s.set(1,330)
    s.set(2,220)
    s.set(3,660)
    time.sleep(2)
    s.clear()
    s.set(0,440)
    s.set(1,330)
    time.sleep(2)
    s.stop()
