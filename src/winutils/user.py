#encoding=utf-8
"""
Define functions for User operations
"""
import os
import logging

from .shell import Shell, REG_CMD

class User(object):
    """
    Define funcitons for common user operations
    """
    @staticmethod
    def username():
        """Get current user name"""
        return os.environ['USERNAME']

    @staticmethod
    def domain():
        """Get user domain"""
        return os.environ['USERDOMAIN']

    @staticmethod
    def auto_admin_consent():
        """
        Allow the Consent Admin to perform an operation
        that requires elevation without consent or credentials
        """
        admin_consent_path = r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'
        cmd1 = r'%s add %s /v ConsentPromptBehaviorAdmin /t REG_DWORD /d 0 /f' % \
               (REG_CMD, admin_consent_path)
        cmd2 = r'%s add %s /v FilterAdministratorToken /t REG_DWORD /d 1 /f' % \
               (REG_CMD, admin_consent_path)
        # Enable UAC(LUA, Limited User Account) to enable metro app
        cmd3 = r'%s add %s /v EnableLUA /t REG_DWORD /d 1 /f' % \
               (REG_CMD, admin_consent_path)
        Shell.system(cmd1)
        Shell.system(cmd2)
        Shell.system(cmd3)

    @staticmethod
    def auto_login(usr_name):
        """Make user login automatically after SUT boot up"""
        logging.debug('%s will login SUT automatically', usr_name)
        winlogon_path = r'HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon'
        cmd1 = r'%s add "%s" /v AutoAdminLogon /t REG_SZ /d 1 /f' % \
               (REG_CMD, winlogon_path)
        cmd2 = r'%s add "%s" /v DefaultUserName /t REG_SZ /d %s /f' % \
               (REG_CMD, winlogon_path, usr_name)
        Shell.system(cmd1)
        Shell.system(cmd2)
