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
import argparse, logging, inspect, os, imp, time

'''
    A getter helper function that probes module 'settings' for a given attribute 'key'.
    If 'key' exists, it returns the value of the attribute.
    If 'key' doesn't exist, this function returns the 'default' value
'''
def getArgument(settings, key, default):
    if key in settings:
        return settings[key]
    return default

'''
    Parse function that adds command line parser groups to the parser and
    populates them with default values, either from attributes of the 'settings' module or as
    last resort sensible default.
'''
def settingsParse(parser, settings):
    # ... required arguments with defaults
    signalprocessinggroup=parser.add_argument_group('signal processing')
    signalprocessinggroup.add_argument('--noofscales',
        type=int,
        help='Specifies the number of scales used in timescale analysis',
        default=getArgument(settings, 'noofscales', 133))
    signalprocessinggroup.add_argument('--inputrate',
        type=int,
        help='Integer sampling rate (Hz) provided by the microphone',
        default=getArgument(settings, 'inputrate', 44100))
    signalprocessinggroup.add_argument('--decimation',
        type=int,
        help='Integer down sampling factor.' ,
        default=getArgument(settings, 'decimation', 5))
    signalprocessinggroup.add_argument('--frequency',
        type=int,
        help='Frequency in Hz to use in publishing microphone data',
        default=getArgument(settings, 'frequency', 2))
    signalprocessinggroup.add_argument('--samplesperframe',
        type=int,
        help='Samples per frame that will be left over after downsampling',
        default=getArgument(settings, 'samplesperframe', 50))
    signalprocessinggroup.add_argument('--whiten', type=float,
        help='Specify whether whitenoise needs to be added and at which intensity.',
        default=None)

    # ... logging behaviour arguments
    behaviourgroup=parser.add_argument_group('logging behaviour')
    behaviourgroup.add_argument('--loglevel',
        type=int,
        help='Loglevels as supported by multiprocessing module',
        default=getArgument(settings, 'loglevel', logging.INFO))
    behaviourgroup.add_argument('--logdir',
        type=str,
        help='Loglevels as supported by multiprocessing module',
        default=getArgument(settings, 'logdir', os.path.expanduser('~')))

    #... input arguments
    inputgroup=parser.add_mutually_exclusive_group()
    inputgroup.add_argument('-n','--whitenoise',
        help='Pass large amount of whitenoise through system',
        action='store_true')
    inputgroup.add_argument('-c','--calibrate',
        help='Initially several processors need to be calibrated, this options runs the necessary code.',
        action='store_true')
    inputgroup.add_argument('-s','--soundfiles',
        help='Specify a python file containg the definition of a soundfiles object: a list of FileAnnotations objects as defined in soundannotator.io.annotations',
        default=None)
    inputgroup.add_argument('-w','--wav',
        help='Specify a wav file',
        default=None)
    inputgroup.add_argument('--sinewave',
        help='Feed sinusoidal signal into system and show response.',
        action='store_true')

    # ... output arguments
    outputgroup=parser.add_argument_group('output modalities')
    outputgroup.add_argument('--outdir',
        help='Output directory for audio data',
        type=str,
        default=os.path.join(os.path.expanduser("~"), ".libsoundannotator"))

    # ... output arguments
    testgroup=parser.add_argument_group('Test and developement options')
    testgroup.add_argument('--test',nargs=1,type=str,
        help='Flag that we are in testing mode.',
        default=None)
   

    # ... ptn arguments
    ptnprocessorgroup=parser.add_argument_group('PTN Processor Options')

    ptnprocessorgroup.add_argument('--PTNE',
        help='Output PTN features',
        action='store_true')
    ptnprocessorgroup.add_argument('--ptnblockwidth', type=float,
        help='Set the blockwidth (in seconds) used for averaging P,T,N, and E ',
        default=getArgument(settings, 'ptnblockwidth', 0.01) )
    ptnprocessorgroup.add_argument('--ptnsplit',
        help='Specify here in a list the boundaries scales at which the P,T,N and E calculations will be split, the range upto the first split and the range upfrom the last split will be discarded from the output because they contain areas for which these features can not be calculated and hence not averaged. ',
        default= getArgument(settings, 'ptnsplit', '[10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120]'))

    ptnprocessorgroup.add_argument('--ptnreferencevalue', type=float,
        help='The ptnreference value is substracted from the rangecompressed E before publication.',
        default=getArgument(settings, 'ptnreferencevalue', None) )

'''
    This function is called as the default hook callback after argparse has parsed the settings.
    It fills more of the arguments using the existing attributes.
    namespace is typically a Namespace class from python's argparse.py
'''
def defaultInternalArgs(namespace):

    namespace.InternalRate = namespace.inputrate / namespace.decimation
    namespace.InternalRate2 = namespace.InternalRate / namespace.samplesperframe

    """
    ChunkSize is dependent on frequency of publishing and inputrate.
    when frequency is for instance 2Hz we want to publish roughly 2 times per second.

    ChunkSize at an InputRate of 48000 would be 24000
    """
    namespace.ChunkSize = namespace.inputrate / namespace.frequency

    return namespace

''' Helper function that populates the namespace of the 'settings' module based on the
    given command line string. This function creates an instance of argparse.ArgumentParser,
    then calls 'settingsParse' which adds parser arguments, and returns...
'''
def populateParser(commandlinestring, settings):
    if not type(settings) == dict:
        raise Exception("Expected 'settings' to be of type 'dict', got {0}".format(type(settings)))

    parser = argparse.ArgumentParser()
    #populate the parser with available arguments
    settingsParse(parser, settings)

    return parser

'''
    Add all the attributes from the namespace's vars() representation to the metadata attribute.
'''
def populateMetaData(commandlinestring,namespace, settings):
    # extract all namespace arguments as dict, assuming namespace is an argparse.Namespace class
    vrs = vars(namespace)
    # create a union of the two dicts, but make sure attributes from the settings metadata override
    # the existing ones from the namespace
    joined = dict(vrs.items() + settings.items())

    joined['commandlinestring']=commandlinestring
    joined['script_started']=time.strftime('%Y-%m-%d-%H-%M')

    setattr(namespace, 'metadata', joined)
    return namespace

'''
    Find a settings module based on a given settings path.
    This function follows the following convention:
        - first it looks if ~/.sa/settings.py exists and if so, it imports that module's settings and returns
        - second it looks if path/filename.py exists and if so, it imports that module's settings and returns
        - third, if neither exist it just returns the sound2sound.config.settings module's settings
'''
def findAndReturnSettingsModule(path, module_name):
    #if $HOME/.sa/<scriptname>_settings.py exists
    if os.path.isfile(os.path.expanduser(os.path.join('~', '.sa', '{0}.py'.format(module_name)))):
        #try to load the module and return it's settings attribute
        try:
            #find_module needs the paths to search in a list
            descriptor = imp.find_module(module_name, [os.path.expanduser(os.path.join('~','.sa'))])
            settings_module = imp.load_module('settings', descriptor[0], descriptor[1], descriptor[2])
            print "Found home dir settings module"
        except:
            raise

    #else, if the folder from where the script is called has a settings file, load that one
    elif os.path.isfile(os.path.join(path, '{0}.py'.format(module_name))):
        try:
            descriptor = imp.find_module(module_name, [path])
            #overwrite default settings file
            settings_module = imp.load_module('settings', descriptor[0], descriptor[1], descriptor[2])
            print "Found settings module in experiment folder"
        except:
            raise

    #else, import the software standard config
    else:
        print "Using software standard settings"
        import settings as settings_module

    if hasattr(settings_module, 'settings'):
        settings = settings_module.settings
    else:
        raise Exception('Specified settings module has no "settings" attribute: {0}'.format(settings_module))

    return settings




''' Return the arguments as parsed by argparse.ArgumentParser().
    The function first tries to retrieve a local settings file based on the pypath kwarg.
    If this file doesn't exist, it imports the local settings file from the same folder as this
    module. Finally, it parses the given command line string based on the settings file
'''
def getArguments(commandlinestring, pypath=None, afterParseHook=defaultInternalArgs):
    if not pypath == None:
        #filename of the script that calls this function without py extension,
        #e.g. 'experiment.py' becomes 'experiment'
        filename = os.path.basename(pypath)
        #append _settings for convention to find a local settings file, e.g. experiment_settings
        settingsfilename = "{0}_settings".format(filename[:-3])
        #the path without the filename
        settingsfilepath = os.path.dirname(pypath)

        '''
            Give back a user-wide settings, or experiment local settings, or software global settings,
            also in that order.
        '''
        settings = findAndReturnSettingsModule(settingsfilepath, settingsfilename)

        #call the parser with registered command line arguments and defaults
        parser = populateParser(commandlinestring, settings)
        #parse the command line string for the args, and pass args to the callback
        #result also includes internal arguments calculated using existing arguments
        if not afterParseHook == None:
            allArgs = afterParseHook(parser.parse_args())
        else:
            allArgs = parser.parse_args()

        #append allArgs with values from settings that are not yet in the namespace
        for key in settings:
            if not key in allArgs:
                setattr(allArgs, key, settings[key])

        #append all the arguments to the 'metadata' attribute
        allArgs = populateMetaData(commandlinestring, allArgs, settings)
        return allArgs

    else:
        raise Exception("kwarg 'pypath' should be specified")


''' Return an absolute filepath given a function in a module.
    This function is convenient for looking up the absolute filepath when given
    a pointer to a function, so it can be used in other modules to pinpoint the
    exact location of the module'''
def abspathFromMethod(method):
    return os.path.abspath(inspect.getsourcefile(method))
