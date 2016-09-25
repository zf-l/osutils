#encoding=utf-8
"""
Define functions to read OS attrubites.
"""
import os
import re
import logging
import subprocess
from collections import namedtuple


WinLicenseStatus = namedtuple('LicenseStatus',
                              ['activated', 'expired', 'remaing_minutes', 'remaing_rearm_count'])


def get_long_bit():
    """
    Check whether this system is 32bit or 64 bit system
    @return:
        32 if OS is 32 bit.
        64 is OS is 64 bit.
    """
    out = os.popen("wmic cpu get addresswidth|more +1")
    bit = "32"
    for line in out.readlines():
        logging.debug('WMIC output: %s', line)
        if line.strip() != "":
            bit = line.strip()
            break
    logging.debug('OS bit: %s', bit)
    return bit


def reboot(timeout=0):
    """Reboot OS"""
    os.system('shutdown -r -t %d' % timeout)

def shutdown(timeout=0):
    """Shutdown OS"""
    os.system('shutdown -s -t %d' % timeout)


def get_license_status(sut):
    """Get Windows Software license status"""
    is_expired = False
    remaing_minutes = 0
    activated = False
    remaing_rearm_count = 0

    dli_cmd = r'cscript c:\Windows\System32\slmgr.vbs -dli //nologo'
    dlv_cmd = r'cscript c:\Windows\System32\slmgr.vbs -dlv //nologo'

    # Execute slmgr.vbs -dli command to check lincense status
    cmd_output = subprocess.check_output(dli_cmd)
    logging.debug('>' + dli_cmd)
    if 'grace time expired' in cmd_output:
        is_expired = True
    elif 'Time remaining:' in cmd_output:
        mat = re.search(r'Time remaining: (?P<min>\d+) minute\(s\)', cmd_output, re.MULTILINE)
        if mat:
            remaing_minutes = int(mat.group('min'))
        else:
            logging.error("Failed to get Time remaining minutes")
            return None
    elif 'License Status: Licensed' in cmd_output:
        activated = True
    else:
        logging.error("Cannot determine Lincense status: %s", cmd_output)
        return None

    # Execute slmgr.vbs -dlv command to get Remaining Windows rearm count
    dlv_output = subprocess.check_output(dlv_cmd)
    logging.debug('>' + dli_cmd)
    logging.debug(sut.dlv_output)

    mat = re.search(r'Remaining Windows rearm count: (?P<rearm_count>\d+)',
                    dlv_output, re.MULTILINE)
    if mat:
        remaing_rearm_count = mat.group('rearm_count')
    else:
        logging.error("Failed to get Remaining Windows rearm count")
        return None

    return WinLicenseStatus(activated, is_expired, remaing_minutes, remaing_rearm_count)


def rearm_windows():
    """Rearm Windows License"""
    rearm_cmd = r'cscript c:\Windows\System32\slmgr.vbs -rearm //nologo'
    return subprocess.check_call(rearm_cmd) == 0
