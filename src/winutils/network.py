"""
Provide functions for network operation
"""
import logging

from .shell import Shell, NETSH_CMD


def disable_firmware():
    "Disable firmware"
    logging.debug('Disable firewall')
    Shell.system("%s firewall set opmode disable" % NETSH_CMD)
