---
license="This file is part of soundannotatordemo. The soundannotatordemo repository
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
"
---
For the microphone at a distance use case we used two RaspberryPi's: a 1B for reading microphone data and a 2B for processing.

We started from scratch with a fresh Raspbian image (2016-09-23-raspbian-jessie-lite) for the 1B.

Steps after install:
- change keyboard layout
- change name to mic
- change password to samic

sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

network={
    ssid="The_ESSID_from_earlier"
    psk="Your_wifi_password"
}


Get the python stuff in place: we used http://geoffboeing.com/2016/03/scientific-python-raspberry-pi/ for inspiration

sudo apt-get update
sudo apt-get upgrade
mkdir manualinstalllog
dpkg -l > ~/manualinstalllog/packages.list


Note: ethernet connection might be needed for part of the upgrade, or correct wifi config.

#Install python basics:
sudo apt-get install build-essential python-dev python-distlib python-setuptools python-pip

pip freeze > ~/manualinstalllog/pip-freeze-initial.list

# Install scientific python packages
sudo apt-get install python-numpy python-scipy python-nose python-pyaudio python-setproctitle python-psutil python-h5py python-redis python-oauthlib python-lz4

# Get FFTW (Works on pi 2b, how about 1b?)
# sudo apt-get install libfftw3-3 libfftw3-dev
# sudo apt-get install python-fftw

pip freeze > ~/manualinstalllog/pip-freeze-with-science.list

sudo apt-get install git

# => image generated from this point


sudo apt-get install cython
sudo apt-get install libhdf5-serial-dev
sudo pip install oauthlib --upgrade

git clone https://github.com/soundappraisal/libsoundannotator.git
git clone https://github.com/soundappraisal/soundannotatordemo.git


cd libsoundannotator
git checkout
git pull origin

python setup.py build install --user test
