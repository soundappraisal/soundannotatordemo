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
import subprocess
import xml.etree.ElementTree as xmltree
import os.path, sys, os
import json
import time

class termcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def generateMetaData():    
    # Determine git status
    try:
        p = subprocess.check_call(["git", "status",'-s'], stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print('**** Exception: {0}.'.format(e))
        print(( '{0}******************************************************************************\n'+
                'Warning: No git repository present in the current working directory:\n'+
                '        {1}\n'+
                'If you\'re building from a source distribution this is expected behaviour\n'+
                'If present the file \'runtimeMetaData.py\' is left unchanged\n'+
                '******************************************************************************{2}').format(termcolors.FAIL, os.getcwd() ,termcolors.ENDC))
        
        return
    
  
    # Open
    runtimeMetaDataFile= open("soundannotatordemo/config/runtimeMetaData.py",'w') # Overwrite previous versions.
    
    # Determine gitstatus
    p = subprocess.Popen(["git","status","-s"], stdout=subprocess.PIPE)
    gitstatus, err = p.communicate()
    #print gitstatus

    # Determine gitversion
    p = subprocess.Popen(["git","show","-s",], stdout=subprocess.PIPE)

    gitversion, err = p.communicate()
    #print gitversion
    commit_hex= gitversion.splitlines()[0].split()[1]
   
    p = subprocess.Popen(["git","rev-parse","--abbrev-ref","HEAD"], stdout=subprocess.PIPE)
    active_branch_name, err = p.communicate()
    active_branch_name=active_branch_name.strip()
    #print active_branch_name
    
    p = subprocess.Popen(["git","config","--get","remote.origin.url"], stdout=subprocess.PIPE)
    url_origin, err = p.communicate()
    url_origin=url_origin.strip()
    #print "url_origin: ", url_origin
    
    p = subprocess.Popen(["git","config","--get","user.name"], stdout=subprocess.PIPE)
    gituser, err = p.communicate()
    gituser=gituser.strip()
    #print "gituser: ", gituser
    
    # ... check whether the workspace is consistent 
    if len(gitstatus) > 0:
        print(('{0}******************************************************************************\n' +   
        'Warning: inconsistent subversion versions in working copy!\n GIT version: {1} \n' + 
        '\nGIT status:\n{2}\n' + 
        '******************************************************************************{3}\n').format(termcolors.WARNING,gitversion,gitstatus,termcolors.ENDC) )
        line = 'outputPathModifier=\'IrreproducibleResult_GIT_{0}\'\n'.format(commit_hex)
    else:
        line = 'outputPathModifier=\'GIT_{0}\'\n'.format(commit_hex)
    print line
    # ... and add the path modifier to the runtime metadata
    runtimeMetaDataFile.write(line)
    
    runtimeMetaData = ""
    runtimeMetaData += 'version = \'{0}\'\n'.format(commit_hex)
    runtimeMetaData += 'branch = \'{0}\'\n'.format(active_branch_name)
    runtimeMetaData += 'remote = \'{0}\'\n'.format(url_origin)
    runtimeMetaData += 'buildtime = \'{0}\'\n'.format(time.ctime())
    runtimeMetaData += 'builddirectory= \'{0}\'\n'.format(os.getcwd())
    runtimeMetaData += 'builtby= \'{0}\'\n'.format(gituser)

    runtimeMetaDataFile.write(runtimeMetaData)

 
if __name__ == '__main__':
    os.chdir('..')
    generateMetaData()
