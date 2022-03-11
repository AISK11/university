# NEMESIS
Network Entity Monitoring Environmental System IssueS

## Installation
### Dependencies
The following packages must be installed:
```
git --version
python3 --version
python3 -m pip --version
```
If any of the following packages is missing, on Debian/Ubuntu distribution can be installed with:
```
sudo apt install git
sudo apt install python3
sudo apt install python3-pip
```

### Installation
Install NEMESIS with:
```
git clone https://github.com/aisk11/nemesis
cd ./nemesis
chmod +x ./install.sh
sudo ./install.sh
sudo bash
source /etc/nemesis/venv/nemesis/bin/activate
python3 -m pip install uptime psutil netifaces netaddr
deactivate && exit
```

## Configure
Configuration file can be found at:

**/etc/nemesis/nemesis_conf.ini**

## Run
To run NEMESIS after it's installed:
```
sudo bash
source /etc/nemesis/venv/nemesis/bin/activate && nemesis.py
```
