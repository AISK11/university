#!/bin/bash

## Script must be run as root.
if [[ ${EUID} -ne 0 ]]; then
    echo "Run as root!"
    exit
fi

################################################################################
#                                '/etc/nemesis'                                #
################################################################################
## Remove '/etc/nemesis' directory.
DIRECTORY="/etc/nemesis"
rm -rf ${DIRECTORY} &&
echo "Directory '${DIRECTORY}' removed." ||
echo "ERROR! Directory '${DIRECTORY}' could not be removed!" ||
exit

## Create '/etc/nemesis' directory.
mkdir ${DIRECTORY} &&
echo "Directory '${DIRECTORY}' created." ||
echo "ERROR! Directory '${DIRECTORY}' could not be created!" ||
exit

################################################################################
#                       '/etc/nemesis/nemesis_conf.ini'                        #
################################################################################
## Generate nemesis config file '/etc/nemesis/nemesis_conf.ini'.
SCRIPT="./install/generate_config.py"
python3 ${SCRIPT} &&
echo "Python script '${SCRIPT}' executed." ||
echo "ERROR! Python script '${SCRIPT}' could not be executed!" ||
exit

################################################################################
#                                   nemesis.py                                 #
################################################################################
## Copy nemesis python script to 'usr/sbin'.
NEMESIS="./install/nemesis.py"
DESTINATION="/usr/sbin"
FULL_PATH="${DESTINATION}/nemesis.py"
cp -f "${NEMESIS}" "${DESTINATION}" &&
echo "Script '${NEMESIS}' copied to '${DESTINATION}'." ||
echo "ERROR! Script '${NEMESIS}' could not be copied to '${DESTINATION}'!" ||
exit

## Change nemesis ownership.
chown root:root "${FULL_PATH}" &&
echo "Ownership of file '${FULL_PATH}' changed to root." ||
echo "ERROR! Ownership of file '${FULL_PATH}' could not be changed to root!" ||
exit

## Make nemesis rights 0500.
chmod 0500 "${FULL_PATH}" &&
echo "Rights of file '${FULL_PATH}' changed to 0500." ||
echo "ERROR! Rights of file '${FULL_PATH}' could not be changed to 0500!" ||
exit

################################################################################
#                                      venv                                    #
################################################################################
## Copy venv to '/etc'/enmesis
VENV="./venv"
cp -rf ${VENV} "${DIRECTORY}" &&
echo "Venv '${VENV}' copied to '${DIRECTORY}'." ||
echo "ERROR! Venv '${VENV}' could not be copied to '${DIRECTORY}'!" ||
exit

## Exit installation.
echo "Installation finished successfully."
