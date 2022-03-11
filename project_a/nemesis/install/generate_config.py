#!/usr/bin/env python3

################################################################################
##                                   README                                   ##
################################################################################
## This script generates configuration file for NEMESIS.
## Configuration file: /etc/nemesis/nemesis_conf.ini


################################################################################
##                                  Modules                                   ##
################################################################################
import configparser


################################################################################
##                              Public Variables                              ##
################################################################################
CONF_FILE = '/etc/nemesis/nemesis_conf.ini'


################################################################################
##                                 Functions                                  ##
################################################################################
def main():
    ## Setup config parser.
    parser = configparser.ConfigParser()

    ## Config parser values.
    parser['nemesis'] = {
        'nemesis_dir': '/etc/nemesis/',
        'interface': 'lo'
    }

    parser['data_pulling'] = {
        'sys_refresh_time':  '30',
        'net_refresh_time': '30'
    }

    ## Write config parser values to file.
    with open(CONF_FILE, 'w') as f:
        parser.write(f)


################################################################################
##                                   Start                                    ##
################################################################################
## Start program.
if __name__ == "__main__":
    main()
