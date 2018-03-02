#!/usr/bin/python

# find microphones using pyAudio 

import pyaudio


class microphoneDetector(object):
    def __init__(self,devicetofind=None):
        self.pa = pyaudio.PyAudio()
        self.device_index = self.detect(devicetofind)

    def stop(self):
        self.stream.close()

    def detect(self,devicetofind):
        print 'devicetofind: {}'.format( devicetofind)
                    
        for i in range( self.pa.get_device_count() ):     
            devinfo = self.pa.get_device_info_by_index(i)   
            print( "Device %d: %s"%(i,devinfo["name"]) )

            
            if devicetofind in devinfo["name"].lower():
                print( "\n Found requested input device %d - %s : %s \n"%(i,devinfo["name"],devinfo) )
  

    
# ... add argument parsing
import sys

if __name__ == "__main__":
    if len(sys.argv) >1:
        devicetofind=sys.argv[1].lower()
    else:
        devicetofind='ALL' # We compare device names in lower case => therefore uppercase string will not match any device
        
    md = microphoneDetector(devicetofind)
    
  

