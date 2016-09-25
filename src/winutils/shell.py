# encoding=utf-8
"""
Define functions for windows shell
"""
import os
import re
import sys
import subprocess
import logging
try:
    import _winreg as winreg
except ImportError:
    import winreg # Python 3

from .winos import get_long_bit


class Shell(object):
    """
    Define funcitons for Windows Shell operations
    """
    @classmethod
    def add2path(cls, dir_path):
        """Add directory to path envrioment
        @param dir_path: Directory path
        """
        reg_key_sys = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
        reg_key_usr = r'Environment'
        reg_val = 'PATH'

        def read_path(key, sub_key):
            """xxx"""
            with winreg.OpenKey(key, sub_key, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as path_key:
                val = winreg.QueryValueEx(path_key, reg_val)[0]
                paths = val.split(os.path.pathsep)
                logging.info('Current PATH variable in %s: %s', sub_key, paths)

                found = False
                tmp_path = [i for i in paths if i.lower() == dir_path.lower()]
                if len(tmp_path) != 0:
                    logging.info(
                        '%s already exist in PATH environment variable', dir_path)
                    found = True

                return found, val

        found1, sys_path = read_path(winreg.HKEY_LOCAL_MACHINE, reg_key_sys)
        if found1:
            return True
        found2 = read_path(winreg.HKEY_CURRENT_USER, reg_key_usr)[0]
        if found2:
            return True

        # Add specified path to envrioment variable
        new_val = sys_path + os.path.pathsep + dir_path
        cmd = r'%(cmd)s add "HKLM\%(key)s" /v %(val_name)s /t REG_EXPAND_SZ /d "%(val)s" /f' % \
              {
                  'cmd': cls.reg_cmd(),
                  'key': reg_key_sys,
                  'val_name': reg_val,
                  'val': new_val
              }
        cls.system(cmd)

    @classmethod
    def system(cls, cmd, expected_code=0, shell=True):
        """Execute a specified application in system shell.
        Return stdout and stderr of application"""
        logging.debug('Execute command: %s', cmd)

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
        out, err = process.communicate()
        ret = process.returncode

        if ret != expected_code:
            desc = '%s failed: %s\nError Message: %s' % (cmd, out, err)
            logging.error(desc)
            raise Exception(desc)

        return out, err

    @staticmethod
    def is_32_bit_process():
        """
        Check whether scripts executed in 32 bit Python
        """
        return '32 bit' in sys.version

    @classmethod
    def where(cls, cmd):
        r"""
        Find command for current OS.
        If user are using Python for x86 on X64 platform,
        x64 version programs are stored under folder:c:\\windows\\sysnative
        """
        os_bit = get_long_bit()
        if os_bit != "32" and cls.is_32_bit_process():
            _pat = re.compile(r'(C:\\Windows\\)(system32)', re.IGNORECASE)

            paths = os.environ['path'].split(os.pathsep)
            paths = [_pat.sub(r'\1sysnative', i)
                     for i in paths if _pat.match(i)]

            for i_path in paths:
                cmd_path = os.path.join(i_path, cmd + '.exe')

                if os.path.exists(cmd_path):
                    logging.debug('Native Command: %s', cmd_path)
                    return cmd_path

        logging.debug('Fail to find command path for %s', cmd)
        return cmd

    @classmethod
    def reg_cmd(cls):
        """
        Get absolute path of reg command
        """
        return cls.where('reg')

    @classmethod
    def hostname(cls, hostname=None):
        """
        Get/Change computer name
        @param hostname: New computer name
        """
        if hostname is None:
            return os.environ['COMPUTERNAME']

        # Change host name to a new name
        reg_values = [
            (r'Control\ComputerName\ActiveComputerName', 'ComputerName'),
            (r'Control\ComputerName\ComputerName', 'ComputerName'),
            (r'services\Tcpip\Parameters', 'Hostname'),
            (r'services\Tcpip\Parameters', 'NV Hostname')
        ]

        for key_name, value_name in reg_values:
            cmd = (r'%s add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\%s"' +
                   r' /v "%s" /t REG_SZ /d %s /f') % \
                  (cls.reg_cmd(), key_name, value_name, hostname)
            os.system(cmd)


# Get native command path
REG_CMD = Shell.where('reg')
NET_CMD = Shell.where('net')
WMIC_CMD = Shell.where('wmic')
NETSH_CMD = Shell.where('netsh')
SCHTASKS_CMD = Shell.where('schtasks')
ROBOCOPY_CMD = Shell.where('robocopy')
MSIEXEC_CMD = Shell.where('msiexec')


if __name__ == '__main__':
    print Shell.where('powershell')
