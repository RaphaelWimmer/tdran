#!/usr/bin/python

from pyeca import *

class Synth:
    def __init__(self, max_channels=1):
        self.e = ECA_CONTROL_INTERFACE()
        self.e.command("cs-add play_chainsetup")
        selected=""
        for i in range(max_channels):
           self.e.command("c-add sin"+str(i))
           #self.e.command("c-select sin"+str(i))
           self.e.command("ai-add null")
           self.e.command("ao-add /dev/dsp")
           print self.e.command("c-selected")
           self.e.command("cop-add el:sine_fcac,440,1")
        
        self.e.command("cs-connect")

    def start(self):
        self.e.command("start")
    
    def stop(self):
        self.e.command("stop")

    def set(self, channel, freq):
        self.e.command("c-select sin"+str(channel))
        self.e.command("cop-select 2")
        self.e.command("copp-select 1")
        self.e.command("copp-set " + str(freq))


if __name__ == "__main__":
    import time
    import sys
    s = Synth(2)
    s.start()
    time.sleep(2)
    s.set(0,440)
    s.set(1,330)
    time.sleep(2)
    s.stop()
