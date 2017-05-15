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
# -*- coding: u8 -*-
import multiprocessing, logging, time, sys, inspect, os, glob
import numpy as np
import signal


# Streamboard architecture
from libsoundannotator.streamboard.board              import Board
from libsoundannotator.streamboard.continuity         import Continuity
from libsoundannotator.streamboard.subscription       import SubscriptionOrder, NetworkSubscriptionOrder

# Streamboard processors
from libsoundannotator.streamboard.processors.input   import noise, sine,  wav
from libsoundannotator.streamboard.processors.input   import  mic_callback as mic 
from libsoundannotator.cpsp                           import oafilterbank
from libsoundannotator.cpsp                           import tfprocessor                 # import GCFBProcessor
from libsoundannotator.cpsp                           import structureProcessor          # import structureProcessor, structureProcessorCalibrator
from libsoundannotator.cpsp                           import patchProcessor              # import patchProcessor, FloorQuantizer, textureQuantizer
from libsoundannotator.cpsp                           import PTN_Processor               # import PTN_Processor




from libsoundannotator.streamboard.processors.output.oldfileout  import FileOutputProcessor


# Version info generated for this build
from  soundannotatordemo.config import runtimeMetaData

# Auxilary software for argument parsing
import soundannotatordemo.config.argparser as argparser

# File information management
from libsoundannotator.io.annotations                 import FileAnnotation

from libsoundannotator.streamboard               import processor

     

def run():

   # Main should initialize logging for multiprocessing package
    logger = multiprocessing.log_to_stderr()
    logger.setLevel(args.loglevel)
    b = Board(loglevel=args.loglevel, logdir=args.logdir, logfile='soundAnnotator') # Setting loglevel is needed under windows
    
    

    def stopallboards(dummy1='1',dummy2='2'):
        b.stopallprocessors()
        time.sleep(1)
        sys.exit('')

    signal.signal(signal.SIGINT, stopallboards)
    
    if args.calibrate or args.whitenoise:
        if args.calibrate:
            ChunkSize=11*args.inputrate
            calibration=True
        else:
            ChunkSize=args.ChunkSize
            calibration=False
        #logger.setLevel(logging.DEBUG)
        b.startProcessor('S2S_SoundInput',noise.NoiseChunkGenerator,
            SampleRate=args.inputrate,
            ChunkSize=ChunkSize,
            metadata=args.metadata,
            noofchunks=100,
            calibration=calibration
        )
    elif args.soundfiles != None:
        with open(args.soundfiles) as fileListGenerator:
            code = compile(fileListGenerator.read(), args.soundfiles, 'exec')
            exec code in locals()
        #execfile(args.soundfiles)
        b.startProcessor('S2S_SoundInput', wav.WavProcessor,
            ChunkSize=args.ChunkSize,
            SoundFiles=soundfiles,
            timestep=0.08,
            AddWhiteNoise=10e-10,
            metadata=args.metadata
        )
    elif args.wav != None:
        if os.path.isdir(args.wav):
            logger.info("WAV argument points to wav folder {0}".format(args.wav))
            wavfiles = glob.glob("{0}/*.wav".format(args.wav))
            if len(wavfiles) == 0:
                raise Exception("Found no wav files in indicated folder")

            logger.info("Found {0} wav files in folder".format(len(wavfiles)))

        elif os.path.isfile(args.wav):
            logger.info("WAV argument points to single wav file")
            wavfiles = [args.wav]
        else:
            logger.error('Invalid specification of wav-file location')
            exit()

        soundfiles = []

        for wavfile in wavfiles:
            soundfiles.append( FileAnnotation(wavfile, wavfile) )

        args.soundfiles=True

        b.startProcessor('S2S_SoundInput', wav.WavProcessor,
            ChunkSize=args.ChunkSize,
            SoundFiles=soundfiles,
            timestep=1,
            metadata=args.metadata,
            AddWhiteNoise=True,
            #newFileContinuity=Continuity.discontinuous
        )
    elif args.sinewave:
        b.startProcessor('S2S_SoundInput', sine.SineWaveGenerator,
            SampleRate=args.inputrate,
            ChunkSize=args.ChunkSize,
            metadata=args.metadata
        )
    else:
        b.startProcessor('S2S_SoundInput', mic.MicInputProcessor,
            SampleRate=args.inputrate,
            ChunkSize=args.ChunkSize,
            nChannels = 1,
            Frequency=args.frequency,
            metadata=args.metadata
        )


    if args.decimation > 1:
        b.startProcessor('S2S_Resampler', oafilterbank.Resampler, SubscriptionOrder('S2S_SoundInput','S2S_Resampler','sound','timeseries'),
            SampleRate=args.inputrate,
            FilterLength=1000,
            DecimateFactor = args.decimation,
            dTypeIn=np.complex64,
            dTypeOut=np.complex64
        )
        myTFProcessorSubscriptionOrder=SubscriptionOrder('S2S_Resampler','S2S_TFProcessor','timeseries','timeseries')
    else:
        myTFProcessorSubscriptionOrder=SubscriptionOrder('S2S_SoundInput','S2S_TFProcessor', 'sound','timeseries')

    samplesPerFrame=args.samplesperframe
    InternalRate=args.inputrate/args.decimation
    InternalRate2=InternalRate/samplesPerFrame

    b.startProcessor('S2S_TFProcessor', tfprocessor.GCFBProcessor, myTFProcessorSubscriptionOrder,
        SampleRate=InternalRate,
        fmin=40,
        fmax=InternalRate/2,
        nseg=args.noofscales,
        samplesPerFrame=samplesPerFrame,
        scale='ERBScale',
        baseOutputDir=args.outdir,
        globalOutputPathModifier=runtimeMetaData.outputPathModifier,
        dTypeIn=np.complex64,
        dTypeOut=np.complex64,
        metadata=args.metadata,
    )


    # Streamboard machine learning


    cachename='S2S_StructureExtractorCache'
    if args.calibrate:
        b.startProcessor('S2S_StructureExtractor',
                          structureProcessor.structureProcessorCalibrator,
                          SubscriptionOrder('S2S_TFProcessor','S2S_StructureExtractor','EdB','TSRep'),
                          noofscales=args.noofscales,
                          cachename=cachename,
                          SampleRate=InternalRate2)
    else:
        b.startProcessor('S2S_StructureExtractor_F',
                          structureProcessor.structureProcessor,
                          SubscriptionOrder('S2S_TFProcessor','S2S_StructureExtractor_F','EdB','TSRep'),
                          noofscales=args.noofscales,
                          cachename=cachename,
                          textureTypes=['f'],
                          SampleRate=InternalRate2)
        b.startProcessor('S2S_StructureExtractor_S',
                          structureProcessor.structureProcessor,
                          SubscriptionOrder('S2S_TFProcessor','S2S_StructureExtractor_S','EdB','TSRep'),
                          noofscales=args.noofscales,
                          cachename=cachename,
                          textureTypes=['s'],
                          SampleRate=InternalRate2)

        if args.PTNE:

            b.startProcessor('S2S_PTNE',PTN_Processor.MaxTract_Processor,
                    SubscriptionOrder('S2S_TFProcessor','S2S_PTNE','E','E'),
                    SubscriptionOrder('S2S_StructureExtractor_F','S2S_PTNE','f_tract','f_tract'),
                    SubscriptionOrder('S2S_StructureExtractor_S','S2S_PTNE','s_tract','s_tract'),
                    featurenames=['pulse','tone','noise','energy','tsmax','tfmax','tsmin','tfmin'],
                    noofscales=args.noofscales,
                    split=eval(args.ptnsplit),
                    SampleRate=InternalRate2,
                    blockwidth=args.ptnblockwidth,
                    ptnreferencevalue = args.ptnreferencevalue,
                )
            '''    '''


            # dump data to file
            #'''
            b.startProcessor("S2S_FileWriter-PTNE", FileOutputProcessor,
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','energy','energy'),
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','pulse','pulse'),
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','noise','noise'),
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','tone','tone'),
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','tsmax','tsmax'),
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','tfmax','tfmax'),
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','tsmin','tsmin'),
                    SubscriptionOrder('S2S_PTNE','S2S_FileWriter-PTNE','tfmin','tfmin'),
                    outdir=os.path.join(args.outdir,runtimeMetaData.outputPathModifier+'-'+args.metadata['script_started'],'ptne'),
                    maxFileSize=args.maxFileSize,
                    datatype = 'float32',
                    requiredKeys=['pulse','tone','noise','energy','tsmax','tfmax','tsmin','tfmin'],
                    #requiredKeys=['pulse','tone','noise','energy','E','f_tract','s_tract'],
                    usewavname=True,
                    metadata=args.metadata,
                )
               
    sleeptime=10
    continuity=Continuity.withprevious

    if args.calibrate:
        toProbeProcessor=b.getConnectionToProcessor(SubscriptionOrder('S2S_StructureExtractor','toProbeProcessor','cacheCreated','cacheCreated'))
        terminationValueContinuity=Continuity.calibrationChunk
    else:
        toProbeProcessor=b.getConnectionToProcessor(SubscriptionOrder('S2S_TFProcessor','toProbeProcessor','technicalkey','technicalkey'))
        terminationValueContinuity=Continuity.last
        sleeptime+=10

    toProbeProcessor.riseConnection(logger)
    toProbeProcessor=toProbeProcessor.connection
    while continuity!=terminationValueContinuity:
        new = toProbeProcessor.poll(0.25)
        if new:
            chunk= toProbeProcessor.recv()
            continuity=chunk.continuity


    print('====================Let processors finish unfinished business====================')
    time.sleep(sleeptime)
    print('====================Wake up and exit====================')
    b.stopallprocessors()


commandlinestring=' '.join(sys.argv)
args = argparser.getArguments(commandlinestring,
                               pypath=argparser.abspathFromMethod(run)
                            )

if __name__ == '__main__':
    run()
