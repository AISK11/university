#!/usr/bin/env python3

################################################################################
##                                   README                                   ##
################################################################################


################################################################################
##                                  Theory                                    ##
################################################################################
'''
GNU/LINUX /sys/class/net/ info:
- https://github.com/torvalds/linux/blob/master/Documentation/ABI/testing/sysfs-class-net
'''


################################################################################
##                          Bugs / Missing Features                           ##
################################################################################
'''
BUGS:
1. Support only for GNU/Linux
2. No disk usage monitoring yet
3. Only first IP address is detected on the interface
4. Only IPv4 supported
5. No speed, frequency, signal strength and BSSID/ESSID detection for wireless.

Cool Ideas:
1. Find if IP address was assigned statically/DHCP/APIPA
'''


################################################################################
##                                  Modules                                   ##
################################################################################
import logging
import configparser
import sys
import os
import errno
import threading
import time
import datetime
## Install: $(python3 -m pip install uptime)
import uptime
## Install: $(python3 -m pip install psutil)
import psutil
import shutil
## Install: $(python3 -m pip install netifaces)
import netifaces
## Install: $(python3 -m pip install netaddr)
import netaddr
import json


################################################################################
##                              Public Variables                              ##
################################################################################
## Hopefully I can keep it clean.


################################################################################
##                                  Classes                                   ##
################################################################################
############################################################
##                      System Info                       ##
############################################################
class SysInfo:
    ########################################
    ##          Operating System          ##
    ########################################
    ## Return string name of operating system.
    ## RETURN:
    ## 'LINUX'
    def os(self):
        if psutil.LINUX:
            return "LINUX"
        elif psutil.WINDOWS:
            return "WINDOWS"
        elif psutil.OSX: ## OSX = MACOS for versions 10.8 to 10.11.
            return "OSX"
        elif psutil.MACOS:
            return "MACOS"
        elif psutil.FREEBSD:
            return "FREEBSD"
        elif psutil.OPENBSD:
            return "OPENBSD"
        elif psutil.NETBSD:
            return "NETBSD"
        elif psutil.BSD:
            return "BSD"
        elif psutil.SUNOS:
            return "SUNOS"
        elif psutil.POSIX:
            return "POSIX"
        else:
            return "UNKNOWN"


    ########################################
    ##         System Date & Time         ##
    ########################################
    ## Return dictionary with date, time and timezone.
    ## RETURN:
    ## {'year': '2022', 'month': '01', 'day': '09', 'hour': '22',
    ## 'minute': '09', 'second': '32', 'timezone_offset': '+0100',
    ## 'timezone': 'CET'}
    def systime_rawdata(self):
        ## Initialize data with default values.
        moment = {
            'year':            '0000',
            'month':           '00',
            'day':             '00',
            'hour':            '00',
            'minute':          '00',
            'second':          '00',
            'timezone_offset': '+0000',
            'timezone':        'NONE'
        }

        ## Get year with century, e.g. 2022.
        moment['year']            = time.strftime('%Y', time.localtime())
        ## Get month [01,12].
        moment['month']           = time.strftime('%m', time.localtime())
        ## Get day [01,31].
        moment['day']             = time.strftime('%d', time.localtime())
        ## Get hour (24-hour clock) [00,23].
        moment['hour']            = time.strftime('%H', time.localtime())
        ## Get minute [00,59].
        moment['minute']          = time.strftime('%M', time.localtime())
        ## Get second [00,59].
        moment['second']          = time.strftime('%S', time.localtime())
        ## Timezone offset from UTC/GMT (+HHMM || -HHMM) [-23:59, +23:59].
        moment['timezone_offset'] = time.strftime('%z', time.localtime())
        ## Timezone name, e.g. CET or CEST (should handle DST automatically).
        moment['timezone']        = time.strftime('%Z', time.localtime())

        ## Return dictionary with date, time and timezone.
        return moment


    ## Return string with current date, time and timezone.
    ## RETURN:
    ## 'YYYY-mm-dd HH:MM:SS +0100 (CET)'
    def systime(self):
        ## Get date, time and timezone data.
        t = self.systime_rawdata()

        ## Return string in format: 'YYYY-mm-dd HH:MM:SS +0100 (CET)'.
        return f"{t['year']}-{t['month']}-{t['day']} "\
            f"{t['hour']}:{t['minute']}:{t['second']} "\
            f"{t['timezone_offset']} ({t['timezone']})"


    ########################################
    ##           System Uptime            ##
    ########################################
    ## Return tuple (days, hours, minutes seconds) since machine started.
    ## RETURN:
    ## (0, 6, 56, 33)
    def uptime_rawdata(self):
        ## Get seconds since PC booted in epoch.
        seconds = int(uptime.uptime()) ## e.g. 24993

        ## Initialize days, hours and minutes to 0.
        days    = 0
        hours   = 0
        minutes = 0

        ## See if there are any days (day has 86400 seconds).
        while seconds >= 86400:
            days    += 1
            seconds -= 86400

        ## See if there are any hours (hour has 3600 seconds).
        while seconds >= 3600:
            hours   += 1
            seconds -= 3600

        ## See if there are any minutes (minute has 60 seconds).
        while seconds >= 60:
            minutes += 1
            seconds -= 60

        ## Return tuple with uptime values.
        return (days, hours, minutes, seconds)


    ## Return string with uptime info.
    ## RETURN:
    ## '0 days, 06:56:33'
    def uptime(self):
        ## Get uptime tuple.
        t = self.uptime_rawdata()

        ## Return string in format: '0 days, 06:56:33'.
        return f"{t[0]} days, {t[1]:02d}:{t[2]:02d}:{t[3]:02d}"


    ## Return boottime string.
    ## RETURN:
    ## 'YYYY-mm-dd HH:MM:SS'
    def boottime(self):
        ## Get time in seconds since the epoch.
        t = psutil.boot_time()

        ## Convert Epoch time to 'YYYY-mm-dd HH:MM:SS'.
        return str(datetime.datetime.fromtimestamp(t))


    ########################################
    ##                CPU                 ##
    ########################################
    ## Return dictionary with physical, logical cores and min, max frequencies.
    ## RETURN:
    ## {'physical_cores': 8, 'logical_cores': 0, 'min_frequency': 800,
    ## 'max_frequency': 4500}
    def cpu_info_rawdata(self):
        ## Initialize data with default values.
        cpu = {
            'physical_cores': 0, ## e.g. 4
            'logical_cores':  0, ## e.g. 8
            'min_frequency':  0, ## e.g. 800  (MHz)
            'max_frequency':  0  ## e.g. 4500 (MHz)
        }

        ## Get physical CPU cores.
        cpu['physical_cores'] = psutil.cpu_count(logical=False)
        ## Get logical CPU cores.
        cpu['physical_cores'] = psutil.cpu_count(logical=True)
        ## Get CPU frequency tuple (current, min, max).
        frequencies            = psutil.cpu_freq(percpu=False)
        ## Get min frequency in MHz.
        cpu['min_frequency']  = int(frequencies[1])
        ## Get max frequency in MHz.
        cpu['max_frequency']  = int(frequencies[2])

        ## Return dictionary with CPU info.
        return cpu


    ## Return float of CPU utilization in percentage [0.0, 100.0].
    ## RETURN:
    ## 27.8
    def cpu_util(self, x: int = 0.1):
        ## Return float of CPU utilization in percentage [0.0, 100.0].
        return psutil.cpu_percent(interval=x, percpu=False)


    ########################################
    ##                RAM                 ##
    ########################################
    ## Return int of RAM size in bytes.
    ## RETURN:
    ## 16646635520
    def ram_size(self):
        ## Return Total RAM size in bytes (divide by 1024 for kiB).
        return psutil.virtual_memory()[0] ## e.g. 16646635520


    ## Return float of RAM utilization in percentage [0.0, 100.0].
    ## RETURN:
    ## 22.8
    def ram_util(self):
        ## Return float of RAM utilization in percentage [0.0, 100.0].
        return psutil.virtual_memory()[2] ## e.g. 22.8


    ########################################
    ##                SWAP                ##
    ########################################
    ## Return int of SWAP size in bytes.
    ## RETURN:
    ## 1027600384
    def swap_size(self):
        ## Return Total SWAP size in bytes (divide by 1024 for kiB).
        return psutil.swap_memory()[0] ## e.g. 1027600384


    ## Return float of SWAP utilization in percentage [0.0, 100.0].
    ## RETURN:
    ## 27.4
    def swap_util(self):
        ## Return float of SWAP utilization in percentage [0.0, 100.0].
        return psutil.swap_memory()[3] ## e.g. 27.4


    ########################################
    ##                Disk                ##
    ########################################
    ## Yet to be added.


############################################################
##                      Network Info                      ##
############################################################
class NetInfo:
    def __init__(self, interface: str = ""):
        ## Passed Interface that will be used in all functions.
        self.interface = interface


    ########################################
    ##           MAC Addresses            ##
    ########################################
    ## Return MAC address of the passed interface as a string.
    ## RETURN:
    ## '4c:f4:5b:1d:08:24'
    ## ERROR RETURN:
    ## 'None'
    def mac(self):
        ## Try to detect MAC address of interface.
        try:
            return netifaces.ifaddresses(self.interface)[netifaces.AF_LINK][0]['addr']
        except Exception:
            return "None"


    ########################################
    ##           IPv4 Addresses           ##
    ########################################
    ## Return first IPv4 address of the passed interface as a string.
    ## RETURN:
    ## '10.0.100.34'
    ## ERROR RETURN:
    ## 'None'
    def ipv4_addr(self):
        ## Try to detect first IPv4 address of interface.
        try:
            return netifaces.ifaddresses(self.interface)[netifaces.AF_INET][0]['addr']
        except Exception:
            return "None"


    ## Return first IPv4 subnet mask of the passed interface as a string.
    ## RETURN:
    ## '255.255.255.0'
    ## ERROR RETURN:
    ## 'None'
    def ipv4_mask(self):
        ## Try to detect first IPv4 subnet mask.
        try:
            return str(netaddr.IPAddress(netifaces.ifaddresses(self.interface)[netifaces.AF_INET][0]['netmask']))
        except Exception:
            return "None"


    ## Return first IPv4 CIDR of the passed interface as a string.
    ## RETURN:
    ## '24'
    ## ERROR RETURN:
    ## 'None'
    def ipv4_cidr(self):
        ## Try to detect first IPv4 CIDR.
        try:
            return str(netaddr.IPAddress(netifaces.ifaddresses(self.interface)[netifaces.AF_INET][0]['netmask']).netmask_bits())
        except Exception:
            return "None"


    ########################################
    ##           IPv6 Addresses           ##
    ########################################
    ## Yet to be added.


    ########################################
    ##            Network Link            ##
    ########################################
    ## Return string if interface is wireless or ethernet.
    ## RETURN:
    ## 'True' || 'False'
    def is_wireless(self):
        file = f"/sys/class/net/{self.interface}/wireless"

        ## Interface is wireless if file exists.
        if os.path.exists(file):
            return "True"
        else:
            return "False"


    ## Return dictionary for specified interface with info for link status.
    ## RETURN:
    ## {'link': 'UP', 'protocol': 'UP', 'carrier': 'UP',
    ## 'wireless': 'False', 'speed': '1000', 'duplex': 'full'}
    ## ERROR RETURN:
    ## {'link': 'UNKNOWN', 'protocol': 'UNKNOWN', 'carrier': 'UNKNOWN',
    ## 'wireless': 'Unknown', 'speed': 'unknown', 'duplex': 'unknown'}
    def link_rawdata(self):
        ## Link data dictionary initialized with default values.
        data = {
            ## Both Ethernet and Wireless properties.
            'link':                   'UNKNOWN', ## UP, DOWN, ADMIN_DOWN, UNKNOWN
            'protocol':               'UNKNOWN', ## UP, DOWN, UNKNOWN
            'carrier':                'UNKNOWN', ## UP, DOWN, ADMIN_DOWN, UNKNOWN
            'wireless':               'Unknown', ## True, False, Unknown
            ## Ethernet only.
            'speed':                  'unknown', ## 0, 100 1000, unknown, none
            'duplex':                 'unknown'  ## full, half, unknown, none
        }

        ## Detect protocol state.
        ## (System tested: Debian GNU/Linux 11, 5.10.0-10-amd64)
        ## N | Carrier (eth) | protocol | operstate | carrier            |
        ## =============================|===========|====================|
        ## 1 | Disconnected  | DOWN     | down      | <Invalid Argument> |
        ## 2 | Disconnected  | UP       | down      | 0                  |
        ## 3 | Connected     | DOWN     | down      | <Invalid Argument> |
        ## 4 | Connected     | UP       | up        | 1                  |
        file = f'/sys/class/net/{self.interface}/carrier'
        ## Protocol is UP, if carrier file is readable.
        try:
            with open(file, 'r') as f:
                ## Read first line.
                f_output = f.read().split('\n')[0]

                ## Protocol is UP.
                data['protocol'] = "UP"
        except Exception:
                ## Protocol is DOWN.
                data['protocol'] = "DOWN"

        ## Detect carrier state.
        file = f'/sys/class/net/{self.interface}/operstate'
        with open(file, 'r') as f:
            ## Read first line.
            f_output = f.read().split('\n')[0]
            ## N | Carrier (eth) | protocol    | operstate  |
            ## ================================|============|
            ## 4 | Connected     | UP          | up (THIS)  |
            if f_output == 'up':
                data['carrier'] = "UP"
            ## N | Carrier (eth) | protocol    | operstate  |
            ## ================================|============|
            ## 2 | Disconnected  | UP (THIS)   | down (THIS)|
            elif (data['protocol'] == "UP") and (f_output == 'down'):
                data['carrier'] = "DOWN"
            ## N | Carrier (eth) | protocol    | operstate  |
            ## ================================|============|
            ## 1 | Disconnected  | DOWN (THIS) | down       |
            ## 3 | Connected     | DOWN (THIS) | down       |
            elif data['protocol'] == "DOWN":
                ## No way how to determine carrier status when protocol is DOWN.
                data['carrier'] = "ADMIN_DOWN"

        ## Detect link status from protocol and carrier.
        if (data['protocol'] == "UP") and (data['carrier'] == "UP"):
            data['link'] = "UP"
        elif (data['protocol'] == "DOWN"):
            data['link'] = "ADMIN_DOWN"
        elif (data['carrier'] == "DOWN"):
            data['link'] = "DOWN"

        ## Detect if link is wireless.
        data['wireless'] = self.is_wireless() ## True || False

        ## Detect link speed.
        ## N | Carrier (eth) | Protocol | speed              |
        ## =============================|====================|
        ## 1 | Disconnected  | DOWN     | <Invalid Argument> |
        ## 2 | Disconnected  | UP       | -1                 |
        ## 3 | Connected     | DOWN     | <Invalid Argument> |
        ## 4 | Connected     | UP       | 1000               |
        if data['wireless'] == "True":
            ## Link speed is not supported for wireless devices.
            data['speed'] = "none"
        else:
            file = f'/sys/class/net/{self.interface}/speed'
            try:
                with open(file, 'r') as f:
                    ## Read first line.
                    f_output = f.read().split('\n')[0]

                    ## If output is '-1', carrier is DOWN, there is no speed.
                    if f_output != '-1':
                        data['speed'] = f_output
            except Exception:
                ## If file could not be opened, keep default 'unknown' value.
                pass

        ## Detect link duplex.
        if data['wireless'] == "True":
            ## Link duplex is not supported for wireless devices.
            data['duplex'] = "none"
        else:
            file = f'/sys/class/net/{self.interface}/duplex'
            try:
                with open(file, 'r') as f:
                    ## Read first line.
                    f_output = f.read().split('\n')[0]

                    data['duplex'] = f_output ## half || full
            except Exception:
                ## If file could not be opened, keep default 'unknown' value.
                pass

        ## Return data as dictionary.
        return data


############################################################
##                        JSON Data                       ##
############################################################
## JsonData class is frontend for pulling info from classes SysInfo and NetInfo.
class JsonData:
    ## Return JSON string containing machine system info.
    ## RETURN:
    ## {"os": "LINUX", "systime": "2022-01-16 23:03:05 +0100 (CET)",
    ## "uptime": "0 days, 08:55:21", "boottime": "2022-01-16 14:07:43",
    ## "cpu_util": 3.7, "ram_util": 21.6, "swap_util": 0.0}
    def sysinfo(self):
        ## Create instance of SysInfo class.
        si = SysInfo()

        data = {
            'os':        si.os(),
            'systime':   si.systime(),
            'uptime':    si.uptime(),
            'boottime':  si.boottime(),
            'cpu_util':  si.cpu_util(),
            'ram_util':  si.ram_util(),
            'swap_util': si.swap_util()
        }

        ## Return dictionary as JSON string.
        return json.dumps(data)


    ## Return JSON string containing info for network interface.
    ## RETURN:
    ## {"interface": "eth0", "mac": "00:2b:67:ad:bb:f6", "ipv4_addr": "None",
    ## "ipv4_mask": "None", "ipv4_cidr": "None", "link": "DOWN",
    ## "protocol": "UP", "carrier": "DOWN", "wireless": "False",
    ## "speed": "unknown", "duplex": "unknown"}
    def netinfo(self, interface: str = ""):
        ## Create instance of NetInfo class for specified interface.
        ni = NetInfo(interface)

        ## Get link data dictionary.
        link = ni.link_rawdata()

        data = {
            'interface':   ni.interface,
            'mac':         ni.mac(),
            'ipv4_addr':   ni.ipv4_addr(),
            'ipv4_mask':   ni.ipv4_mask(),
            'ipv4_cidr':   ni.ipv4_cidr(),
            'link':        link['link'],     ## UP, DOWN, ADMIN_DOWN, UNKNOWN
            'protocol':    link['protocol'], ## UP, DOWN, UNKNOWN
            'carrier':     link['carrier'],  ## UP, DOWN, ADMIN_DOWN, UNKNOWN
            'wireless':    link['wireless'], ## True, False, Unknown
            'speed':       link['speed'],    ## 0, 100 1000, unknown, none
            'duplex':      link['duplex'],   ## full, half, unknown, none
        }

        ## Return dictionary as JSON string.
        return json.dumps(data)


    ## This function keep writing SysInfo JSON string to specified file every
    ## X (specified) seconds.
    ## (Use thread for this function.)
    def write_sysinfo(self, file: str, wait_time: int):
        while True:
            ## Data that has to be written (JSON string).
            data = self.sysinfo()

            ## Write JSON string to file.
            with open(file, "w") as f:
                f.write(data)
                logging.debug(f"Written JSON data to \'{file}\'.")

            ## Wait until next write request is needed.
            time.sleep(wait_time)


    ## This function keep writing NetInfo JSON string for specified interface
    ## to specified file every X (specified) seconds.
    ## (Use thread for this function.)
    def write_netinfo(self, file: str, wait_time: int, interface: str):
        while True:
            ## Data that has to be written (JSON string).
            data = self.netinfo(interface)

            ## Write JSON string to file.
            with open(file, "w") as f:
                f.write(data)
                logging.debug(f"Written JSON data to \'{file}\'.")

            ## Wait until next write request is needed.
            time.sleep(wait_time)


################################################################################
##                                 Functions                                  ##
################################################################################
############################################################
##                     Initialization                     ##
############################################################
########################################
##            Runtime Logs            ##
########################################
## Initialize logging.
## ERROR RETURN:
## sys.exit
def start_logging(loglevel: int = logging.INFO):
    try:
        ## Set up basic logging config as following:
        ## CRITICAL (50), ERROR (40), WARNING (30), INFO (20), DEBUG (10)
        logging.basicConfig(
            ## Set level, since which logs should be output (Default: WARNING).
            level = loglevel,
            ## Specify format of log messages:
            ## YYYY-mm-dd hh:MM:SS,sss [LEVEL] - MESSAGE
            format = '%(asctime)s [%(levelname)s] - %(message)s'
        )
    except Exception:
        ## Print error message to stderr.
        printf(f"ERROR! Logging could not be set up!", file=sys.stderr)

        # Exit with error code of 'No such file or directory'.
        sys.exit(errno.ENOENT)


########################################
##          Root Permission           ##
########################################
## Check if user has root privileges.
## ERROR RETURN:
## sys.exit
def rootcheck():
    ## See if user has UID 0 (root).
    if os.getuid() != 0:
        logging.critical(f"Root privileges required! Exiting.")

        ## Exit with error code of 'Operation not permitted'.
        sys.exit(errno.EPERM)


########################################
##            Config file             ##
########################################
## Return configuration from config file as dictionary.
## RETURN:
## {'nemesis_dir': '/etc/nemesis/', 'interface': 'lo',
## 'sys_refresh_time': '30', 'net_refresh_time': '30'}
def load_config():
    ## Conf file: '/etc/nemesis/nemesis_conf.ini'.
    file = '/etc/nemesis/nemesis_conf.ini'

    ## Setup config parser.
    parser = configparser.ConfigParser()

    ## Dictionary data from config file (filled with default values).
    conf = {
        'nemesis_dir':      '/etc/nemesis/',
        'interface':        'lo',
        'sys_refresh_time': '30',
        'net_refresh_time': '30'
    }

    ## Try to read config file.
    try:
        ## Read config file.
        parser.read(file)

        ## Get values from config file.
        conf['nemesis_dir']      = parser.get('nemesis',      'nemesis_dir',      fallback='/etc/nemesis/')
        conf['interface']        = parser.get('nemesis',      'interface',        fallback='lo')
        conf['sys_refresh_time'] = parser.get('data_pulling', 'sys_refresh_time', fallback='30')
        conf['net_refresh_time'] = parser.get('data_pulling', 'net_refresh_time', fallback='30')

        ## Return dictionary with data loaded from config file.
        return conf
    except Exception:
        logging.error(f"Configuration file \'{file}\' could not be read! Using default values instead.")

        ## Return dictionary with default config data.
        return conf


## Creates data directories for IPv4 and IPv6 and return directory path as
## strings in a tuple.
## RETURN:
## ('/etc/nemesis/nemesis_data/json/ipv4', '/etc/nemesis/nemesis_data/json/ipv6')
def create_data_dirs(parent_dir: str):
    ## Remove trailing '/'s for passed directory.
    while parent_dir[-1] == '/':
        ## Remove last character in a string.
        parent_dir = parent_dir[:-1]

    ## Check if passed directory exists.
    if not os.path.isdir(parent_dir):
        if not os.path.exists(parent_dir):
            logging.critical(f"Directory \'{parent_dir}\' does not exists! Exiting.")

            ## Exit with error code of 'No such file or directory'.
            sys.exit(errno.ENOENT)
        else:
            logging.critical(f"File \'{parent_dir}\' is not a directory! Exiting.")

            ## Exit with error code of 'No such file or directory'.
            sys.exit(errno.ENOENT)

    ## Remove data directory if it exists (to prevent old data).
    data_dir = f"{parent_dir}/nemesis_data"
    if os.path.exists(f"{data_dir}"):
        ## Check if it is file.
        if os.path.isfile(f"{data_dir}"):
            ## Remove file.
            os.remove(data_dir)
            logging.debug(f"File \'{data_dir}\' removed.")
        else:
            ## Remove directory with all files inside it.
            shutil.rmtree(data_dir)
            logging.debug(f"Directory \'{data_dir}\' removed.")

    ## Create new empty data directory.
    os.mkdir(data_dir)
    logging.debug(f"Directory \'{data_dir}\' created.")

    ## Create directory for JSON data.
    os.mkdir(f"{data_dir}/json")
    logging.debug(f"Directory \'{data_dir}/json\' created.")

    ## Create directory for monitoring IPv4 network hosts.
    os.mkdir(f"{data_dir}/json/ipv4")
    logging.debug(f"Directory \'{data_dir}/json/ipv4\' created.")

    ## Create directory for monitoring IPv6 network hosts.
    os.mkdir(f"{data_dir}/json/ipv6")
    logging.debug(f"Directory \'{data_dir}/json/ipv6\' created.")

    ## Return tuple with IPv4 and IPv6 directory locations as strings.
    return (f"{data_dir}/json/ipv4", f"{data_dir}/json/ipv6")


def main():
    ## Initialize logging.
    start_logging(logging.DEBUG)
    logging.info("Nemesis started.")

    ## Check if user has root privileges.
    rootcheck()

    ## Load configuration from config file to dictionary variable.
    config = load_config()
    logging.debug(f"Configuration file settings: {config}.")

    ## Get tuple of data dirs e.g.
    ## ('/etc/nemesis/nemesis_data/json/ipv4', '/etc/nemesis/nemesis_data/json/ipv6')
    data_dirs = create_data_dirs(config['nemesis_dir'])

    ## Nemesis IPv4 sysinfo file.
    n4sf = f"{data_dirs[0]}/nemesis_sys.json"
    ## Nemesis IPv4 netinfo file.
    n4nf = f"{data_dirs[0]}/nemesis_net.json"
    ## Nemesis IPv6 sysinfo file.
    n6sf = f"{data_dirs[1]}/nemesis_sys.json"
    ## Nemesis IPv6 netinfo file.
    n6nf = f"{data_dirs[1]}/nemesis_net.json"

    ## Create instance of JsonData class.
    json_data = JsonData()

    ## Create threads to keep writing JSON data.
    thd_1 = threading.Thread(target=json_data.write_sysinfo, args=(n4sf, int(config['sys_refresh_time']),))
    thd_2 = threading.Thread(target=json_data.write_netinfo, args=(n4nf, int(config['net_refresh_time']), config['interface'],))

    ## Start threads (this will keep happening until process is stopped/killed).
    thd_1.start()
    thd_2.start()


################################################################################
##                                   Start                                    ##
################################################################################
## Start program.
if __name__ == "__main__":
    main()
