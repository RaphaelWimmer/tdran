#!/usr/bin/python

from pyeca import *
from threading import *
import time


def unique(s):
    """Return a list of the elements in s, but without duplicates.

    For example, unique([1,2,3,1,2,3]) is some permutation of [1,2,3],
    unique("abcabc") some permutation of ["a", "b", "c"], and
    unique(([1, 2], [2, 3], [1, 2])) some permutation of
    [[2, 3], [1, 2]].

    For best speed, all sequence elements should be hashable.  Then
    unique() will usually work in linear time.

    If not possible, the sequence elements should enjoy a total
    ordering, and if list(s).sort() doesn't raise TypeError it's
    assumed that they do enjoy a total ordering.  Then unique() will
    usually work in O(N*log2(N)) time.

    If that's not possible either, the sequence elements must support
    equality-testing.  Then unique() will usually work in quadratic
    time.
    """

    n = len(s)
    if n == 0:
        return []

    # Try using a dict first, as that's the fastest and will usually
    # work.  If it doesn't work, it will usually fail quickly, so it
    # usually doesn't cost much to *try* it.  It requires that all the
    # sequence elements be hashable, and support equality comparison.
    u = {}
    try:
        for x in s:
            u[x] = 1
    except TypeError:
        del u  # move on to the next method
    else:
        return u.keys()

    # We can't hash all the elements.  Second fastest is to sort,
    # which brings the equal elements together; then duplicates are
    # easy to weed out in a single pass.
    # NOTE:  Python's list.sort() was designed to be efficient in the
    # presence of many duplicate elements.  This isn't true of all
    # sort functions in all languages or libraries, so this approach
    # is more effective in Python than it may be elsewhere.
    try:
        t = list(s)
        t.sort()
    except TypeError:
        del t  # move on to the next method
    else:
        assert n > 0
        last = t[0]
        lasti = i = 1
        while i < n:
            if t[i] != last:
                t[lasti] = last = t[i]
                lasti += 1
            i += 1
        return t[:lasti]

    # Brute force is all that's left.
    u = []
    for x in s:
        if x not in u:
            u.append(x)
    return u


class Synth(Thread):
    def __init__(self, channels=1):
        Thread.__init__(self)
        self.channels = channels
        self.freqs = [0] * channels
        self.running = True
        self.command_queue = []
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
        #self.start() # start thread
        #print self.e.command("c-status")

    def start_synth(self):
        self.e.command("start")
        self.running = True
        self.start()
    
    def stop_synth(self):
        self.e.command("stop")
        self.running = False
        self.command_queue = []

    def set(self,channel,freq):
        if self.running:
            self.command_queue.append(("set",channel,int(freq)))

    def thr_set(self, channel, freq):
        if freq in self.freqs or channel >= self.channels:
            return
        else:
            self.e.command("c-select sin"+str(int(channel)))
            self.e.command("cop-select 2")
            self.e.command("copp-select 1")
            self.e.command("copp-set " + str(freq))
            self.freqs[channel] = freq
        
    def clear(self):    
        if self.running:
            self.command_queue.append(("clear",))

    def thr_clear(self):
        if len(self.command_queue) > 5:
            self.command_queue = self.command_queue[0:5]
        for i in range(self.channels):
            self.e.command("c-select sin"+str(i))
            self.e.command("cop-select 2")
            self.e.command("copp-select 1")
            self.e.command("copp-set " + str(0))

    def run(self):
        while self.running:
            time.sleep(0.1)
            #self.command_queue = unique(self.command_queue)
            print self.command_queue
            if len(self.command_queue) > 0:
                cmd = self.command_queue.pop(0)
                print self.command_queue
                if cmd[0] == "set":
                    self.thr_set(cmd[1],cmd[2])
                elif cmd[0] == "clear":
                    self.thr_clear()

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
