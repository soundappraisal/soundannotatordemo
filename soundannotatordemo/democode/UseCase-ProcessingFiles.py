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
'''

    Script demonstrating the Processing Files use case of the libsoundannotator software.
    

'''

import multiprocessing
import numpy as np

# signal is used to handle keyboard interrupts, in this case ^C^C which is used to stop the board using sys.exit.
import signal, sys


import time,  os, glob

# Streamboard architecture
from libsoundannotator.streamboard.board                            import Board
from libsoundannotator.streamboard.continuity                       import Continuity
from libsoundannotator.streamboard.subscription                     import SubscriptionOrder

# Streamboard processors
from libsoundannotator.streamboard.processors.input                 import noise, wav 
from libsoundannotator.cpsp                                         import oafilterbank_numpy as oafilterbank
from libsoundannotator.cpsp                                         import tfprocessor               
from libsoundannotator.cpsp                                         import structureProcessor 

from libsoundannotator.cpsp                                         import PTN_Processor               
from libsoundannotator.streamboard.processors.output.oldfileout     import FileOutputProcessor


# Version info generated for this build
from  soundannotatordemo.config import runtimeMetaData

# File information management
from libsoundannotator.io.annotations                   import FileAnnotation

def run():

    # Main should initialize logging for multiprocessing package
    logger = multiprocessing.log_to_stderr()
    logger.setLevel(args['loglevel'])
    
    # Create the board from which all processes will be created
    b = Board(loglevel=args['loglevel'], logdir=args['logdir'], logfile='soundAnnotator') 

    # ... and add the ability to stop it manually in a neat way.
    def stopallboards(dummy1='1',dummy2='2'):
        b.stopallprocessors()
        time.sleep(1)
        sys.exit('')

    signal.signal(signal.SIGINT, stopallboards)


    # Generate input from:
    #     -  generated calibration noise to estimate parameters 
    #     -  a directory with wav-files or an individual wav-file
    if args['calibrate']:
        # Start generating noise
        #   SampleRate ; sampling frequency
        #   ChunkSize: number of samples produced in one iteration, should be large for calibration.
        #   metadata:   anything the developer deems relevant to propagate  
        #   noofchunks: number of chunks produced before it stops, if set to None it might go on and on
        #   calibration: if set to true settings will be imposed fitting this use case.
        ChunkSize=11*args['inputrate']
        b.startProcessor('S2S_SoundInput',noise.NoiseChunkGenerator,
            SampleRate=args['inputrate'],
            ChunkSize=ChunkSize,
            metadata=args,
            noofchunks=1,
            calibration=args['calibrate'],  # Will force noofchunks to 1 and fixes continuity
        )
    elif args['wav'] != None:
        if os.path.isdir(args['wav']):
            logger.info("WAV argument points to wav folder {0}".format(args['wav']))
            wavfiles = glob.glob("{0}/*.wav".format(args['wav']))
            if len(wavfiles) == 0:
                raise Exception("Found no wav files in indicated folder")
            logger.info("Found {0} wav files in folder".format(len(wavfiles)))
        elif os.path.isfile(args['wav']):
            logger.info("WAV argument points to single wav file")
            wavfiles = [args['wav']]
        else:
            logger.error('Invalid specification of wav-file location')
            exit()

        soundfiles = []

        # The soundfile path is wrapped in a FileAnnotation object,
        # this allows for recombining libsoundannotator output with 
        # annotations.
        for wavfile in wavfiles:
            soundfiles.append( FileAnnotation(wavfile, wavfile) )

        # Start reading wav-files. 
        #   chunksize:  the number of samples read from file.
        #   soundfiles: list with references to wav-files
        #   timestep:   publication interval in seconds
        #   metadata:   anything the developer deems relevant to propagate  
        #   AddWhiteNoise=None   : some wav-files contain ling silence, this breaks log energy 
        #   newFileContinuity=Continuity.newfile  : default continuity for newfiles
        #   startLatency=1.0   : delay first read to allow board to build other processors
        b.startProcessor('S2S_SoundInput', wav.WavProcessor,
            ChunkSize=args['chunksize'],
            SoundFiles=soundfiles,
            timestep=0.08,
            metadata=args,
            #newFileContinuity=Continuity.discontinuous
        )
    else:
        logger.info("Nothing to process: leaving script!")
        sys.exit("Nothing to process: leaving script!")


    if args['decimation'] > 1:
        
        # Start resampling. 
        #   KaiserBeta=5      : Kaiser window beta
        #   FilterLength=60   : Length lowpass filter
        #   DecimateFactor=5  : Target decimation factor
        #   SampleRate:         sampling frequency
        #   dTypeIn:            numerical format incoming samples
        #   dTypeOut:           numerical format outgoing samples
        b.startProcessor('S2S_Resampler', oafilterbank.Resampler, SubscriptionOrder('S2S_SoundInput','S2S_Resampler','sound','timeseries'),
            SampleRate=args['inputrate'],
            FilterLength=1000,
            DecimateFactor = args['decimation'],
            dTypeIn=np.complex64,
            dTypeOut=np.complex64
        )
        myTFProcessorSubscriptionOrder=SubscriptionOrder('S2S_Resampler','S2S_TFProcessor','timeseries','timeseries')
    else:
        myTFProcessorSubscriptionOrder=SubscriptionOrder('S2S_SoundInput','S2S_TFProcessor', 'sound','timeseries')

    # Resampling changed the sampling frequency, so processor taking data from the Resampler need to use the following sampling frequency
    InternalRate=args['inputrate']/args['decimation']

    # The gammachirp filterbank will do a further decimation. As we only keep the complex amplitude we effectively
    # do a kind of conversion to a lower frequency. This is not fully developed theoretically but it seems to work 
    # for small decimations. (Note "frame" is not proper terminology, but used here for historical reason.)  
    samplesPerFrame=args['samplesperframe']
    InternalRate2=InternalRate/samplesPerFrame

    
    # Start cochleogram calculation 
    #   Input parameters:
    #       SampleRate:         sampling frequency
    #       dTypeIn:            numerical format incoming samples
    #   Output parameters:
    #       dTypeOut:           numerical format outgoing samples
    #       samplesPerFrame=samplesPerFrame  : decimation factor 
    #   TF-Processing parameters
    #       fmin=40,            : lowest frequency used in TF analysis
    #       fmax=InternalRate/2 : highest frequency used in TF analysis
    #       nseg=args['noofscales']    : number of different frequenccies used
    #       scale='ERBScale':  'loglin' or 'ERB' equivalent rectangular bandwidth
    #   Parameter storage (obsolete but working):
    #       baseOutputDir=args['outdir'] : location where GCFBProcessor parameters will be saved
    #       globalOutputPathModifier : modifies location where GCFBProcessor parameters will be saved based on GIT commit sha
    #   metadata:   anything the developer deems relevant to propagate      
    b.startProcessor('S2S_TFProcessor', tfprocessor.GCFBProcessor, myTFProcessorSubscriptionOrder,
        SampleRate=InternalRate,
        fmin=40,
        fmax=InternalRate/2,
        nseg=args['noofscales'],
        samplesPerFrame=samplesPerFrame,
        scale='ERBScale',
        baseOutputDir=args['outdir'],
        globalOutputPathModifier=runtimeMetaData.outputPathModifier,
        dTypeIn=np.complex64,
        dTypeOut=np.complex64,
        metadata=args,
    )


    # Streamboard feature extraction
    cachename='S2S_StructureExtractorCache'
    if args['calibrate']:
        # Start calibration structure extraction
        #   The structure extractor needs to know the correlation length in white noise,
        #   these are calculated in this calibration step and then cached.
        b.startProcessor('S2S_StructureExtractor',
                          structureProcessor.structureProcessorCalibrator,
                          SubscriptionOrder('S2S_TFProcessor','S2S_StructureExtractor','EdB','TSRep'),
                          noofscales=args['noofscales'],
                          cachename=cachename,
                          SampleRate=InternalRate2)
    else:
        # Start structure extraction for pulses 
        #   textureTypes=['f']   'f' is oriented center surround ratio's in the frame direction => high for pulses
        #   SampleRate : sample frequency of incoming signal
        #   noofscales: number of different frequencies used in incoming TF-representation
        #   cachename : name of the file containing the calculated calibration parameters 
        b.startProcessor('S2S_StructureExtractor_F',
                          structureProcessor.structureProcessor,
                          SubscriptionOrder('S2S_TFProcessor','S2S_StructureExtractor_F','EdB','TSRep'),
                          noofscales=args['noofscales'],
                          cachename=cachename,
                          textureTypes=['f'],
                          SampleRate=InternalRate2)
                          
        # Start structure extraction for tones 
        #   textureTypes=['s']   's' is oriented center surround ratio's in the scale direction => high for tones
        #   SampleRate : sample frequency of incoming signal
        #   noofscales: number of different frequencies used in incoming TF-representation
        #   cachename : name of the file containing the calculated calibration parameters 
        b.startProcessor('S2S_StructureExtractor_S',
                          structureProcessor.structureProcessor,
                          SubscriptionOrder('S2S_TFProcessor','S2S_StructureExtractor_S','EdB','TSRep'),
                          noofscales=args['noofscales'],
                          cachename=cachename,
                          textureTypes=['s'],
                          SampleRate=InternalRate2)

        # Start calculation of PTNE featuress 
        #       featurenames        : subset of ['pulse','tone','noise','energy'],
        #       noofscales          : number of frequencies in incoming TF -representation
        #       split               : string specifying boundary between frequency bands used in creating blocks
        #       SampleRate          : input sampling frequency
        #       blockwidth          : timeinterval included in calculation of a block
        #       ptnreferencevalue   : value subtracted from the range compressed E before publishing
        b.startProcessor('S2S_PTNE',PTN_Processor.PartialPTN_Processor,
                SubscriptionOrder('S2S_TFProcessor','S2S_PTNE','E','E'),
                SubscriptionOrder('S2S_StructureExtractor_F','S2S_PTNE','f_tract','f_tract'),
                SubscriptionOrder('S2S_StructureExtractor_S','S2S_PTNE','s_tract','s_tract'),
                featurenames=['pulse','tone','noise','energy'],
                noofscales=args['noofscales'],
                split=eval(args['ptnsplit']),
                SampleRate=InternalRate2,
                blockwidth=args['ptnblockwidth'],
                ptnreferencevalue = args['ptnreferencevalue'],
            )



        # Start writing PTNE  features to file
        b.startProcessor("S2S_FileWriter-PTNE", FileOutputProcessor,
                SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','energy','energy'),
                SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','pulse','pulse'),
                SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','noise','noise'),
                SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','tone','tone'),
                outdir=os.path.join(args['outdir'],runtimeMetaData.outputPathModifier+'-'+args['script_started'],'ptne'),
                maxFileSize=args['maxFileSize'],
                datatype = 'float32',
                requiredKeys=['pulse','tone','noise','energy'],
                usewavname=True,
                metadata=args,
            )

        # Start writing tract features and cochleogram to file
        # ... a second file writer is needed because PTNE publishes at another rate then the preceding processors.
        b.startProcessor("S2S_FileWriter-Tracts", FileOutputProcessor,
                SubscriptionOrder('S2S_TFProcessor','S2S_FileWriter-Tracts','EdB','EdB'),
                SubscriptionOrder('S2S_StructureExtractor_F','S2S_FileWriter-Tracts','f_tract','f_tract'),
                SubscriptionOrder('S2S_StructureExtractor_S','S2S_FileWriter-Tracts','s_tract','s_tract'),
                outdir=os.path.join(args['outdir'],runtimeMetaData.outputPathModifier+'-'+args['script_started'],'tracts'),
                maxFileSize=args['maxFileSize'],
                datatype = 'float32',
                requiredKeys=['E','f_tract','s_tract'],
                usewavname=True,
                metadata=args,
            )
        
       

    # ========= Code monitoring for spotting the termination condition and initiating subsequent clean-up =======
    
    # Set up connections to indicative processors.
    if args['calibrate']:
        toProbeProcessor=b.getConnectionToProcessor(SubscriptionOrder('S2S_StructureExtractor','toProbeProcessor','cacheCreated','cacheCreated'))
        terminationValueContinuity=Continuity.calibrationChunk
        sleeptime=1
    else:
        toProbeProcessor=b.getConnectionToProcessor(SubscriptionOrder('S2S_TFProcessor','toProbeProcessor','technicalkey','technicalkey'))
        terminationValueContinuity=Continuity.last
        sleeptime=10

    # Make obtained connections usable 
    toProbeProcessor.riseConnection(logger)
    toProbeProcessor=toProbeProcessor.connection
    
    # Watch for a change in continuity consistent with a termination condition. 
    continuity=Continuity.withprevious
    while continuity!=terminationValueContinuity:
        new = toProbeProcessor.poll(0.25)
        if new:
            chunk= toProbeProcessor.recv()
            continuity=chunk.continuity

    # Give processors time to finish their business and stop them all.
    print('====================Let processors finish unfinished business====================')
    time.sleep(sleeptime)
    print('====================Wake up and exit====================')
    b.stopallprocessors()
    


if __name__ == '__main__':
    args=dict()

    # Set logging parameters
    basedir=os.path.join(os.path.expanduser('~'),'.libsoundannotator')
    if not os.path.isdir(basedir):
        os.mkdir(basedir)
    import logging
    args['loglevel']=logging.INFO
    args['logdir']=os.path.join(basedir,'log')
    if not os.path.isdir(args['logdir']):
        os.mkdir(args['logdir'])


    # Set wavfile related parameters
    args['inputrate']=44100
    
    args['wav']=os.path.join(os.path.abspath('..'),'demodata','dares_g1')
    location= raw_input('Please provide the path to the wav-files (defaults to {0}): '.format(args['wav']))
    if not location =='':
        args['wav']=location
        
    #metadata passed along with all chunks
    args['script_started']=time.strftime('%Y-%m-%d-%H-%M')

    # Parameters for Resampler
    args['decimation']=1
    args['chunksize']=8820

    # Parameters for TF-Processor
    args['noofscales']=100
    args['samplesperframe']=5

    # Parameters PTN-Processor
    args['ptnsplit']= '[5,20,35,50,65,80,95]'  # string, with list which divides the TF-plane in frequency bands, 
                                             # the TF-plane outside the first and last sacale is ignored.
    args['ptnblockwidth']=0.1                # timeinterval over which summing takes place.
    args['ptnreferencevalue']= None          # ptnreferencevalue will be subtracted before publishing rangecompressed bandmeans of E

    # Parameters FileWriter
    args['maxFileSize']=104857600            # in bytes


    # output directory
    args['outdir']=os.path.join(basedir,'results')
    if not os.path.isdir(args['outdir']):
        os.mkdir(args['outdir'])

    args['calibrate']=True
    run()
    args['calibrate']=False
    run()