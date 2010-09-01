#!/usr/bin/python

from pyeca import *

class Synth:
    def __init__(self, freq=440):
        self.e = ECA_CONTROL_INTERFACE()
        self.e.command("cs-add play_chainsetup")
        self.e.command("c-add 1st_chain")
        self.e.command("ai-add null")
        self.e.command("ao-add /dev/dsp")
        self.e.command("cop-add el:sine_fcac,"+ str(freq) + ",1")
        self.e.command("cs-connect")
        self.e.command("cop-select 2")
        self.e.command("copp-select 1")

    def start(self):
        self.e.command("start")
    
    def stop(self):
        self.e.command("stop")

    def set(self, freq):
        self.e.command("copp-set " + str(freq))


if __name__ == "__main__":
    import time
    import sys
    s = Synth()
    if len(sys.argv) > 1:
        s.set(int(sys.argv[1]))
    else:
        s.set(440)
    s.start()
    time.sleep(2)
    s.stop()
