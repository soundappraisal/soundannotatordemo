'''
This file is part of soundannotatordemo. The soundannotatordemo repository
provides democode and documentation accompanying the libsoundannotator 
repository, available from https://github.com/soundappraisal/libsoundannotator.
The library libsoundannotator is designed for processing sound using 
time-frequency representations.

Copyright 2011-2014 Sensory Cognition Group, University of Groningen
Copyright 2014-2017 SoundAppraisal BV

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
import numpy as np
import os 

settings = {
    'receiverkey' : 'dataout',
    'maxFileSize' : 104857600, #in bytes
    'location' : os.path.join(os.path.expanduser('~'),'data','libsoundannotator','hdfdump_location'),
    'ptnreferencevalue' : 0.0, # Assume split [10,60] , blockwidth=0.005, fs=44100, 20/np.log(10)*np.log10(2/(50*44100*0.005/25)) 
}
