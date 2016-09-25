# encoding=utf-8

"""
Read/Modify settings in Windows task configuration file
"""

import re
from xml.etree import ElementTree
import logging

from .shell import Shell, SCHTASKS_CMD

_TASK_CFG_TEMPLATE = '''<?xml version="1.0"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2013-05-20T18:34:39</Date>
    <Author>%(user)s</Author>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>%(user)s</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>false</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>P3D</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>%(command)s</Command>
    </Exec>
  </Actions>
</Task>'''


class TaskCfgFile(object):
    """
    This class read/configure settings in Windows task configuration file
    """

    def __init__(self, file_path):
        logging.debug('XMl file path: %s', file_path)

        self.cfg_file = file_path
        self.xml = None
        self.usr_node = None
        self.cmd_node = None
        self.author_node = None
        self.xmlns = None
        self._saved = True

    def load(self):
        """Load and parse xml file"""
        self.xml = ElementTree.parse(self.cfg_file)
        logging.debug('Reading setttings form %s', self.cfg_file)

        root_tag = self.xml.getroot().tag
        match_obj = re.match('{([^{}]+)}', root_tag)
        xmlns = ''
        if match_obj is not None:
            xmlns = match_obj.group(1)
            logging.debug('XML namespace: %s', xmlns)
            ElementTree.register_namespace('', xmlns)

        # Read user information
        usr_path = self._abs_path('./Principals/Principal/UserId', xmlns)
        usr_node = self.xml.find(usr_path)
        if usr_node is None:
            msg = 'File Format Error: Fail to find "%s" in %s' % (
                usr_path, self.cfg_file)
            logging.error(msg)
            raise Exception(msg)

        cmd_path = self._abs_path('./Actions/Exec/Command', xmlns)
        cmd_node = self.xml.find(cmd_path)
        if cmd_node is None:
            msg = 'File Format Error: Fail to find "%s" in %s' % (
                cmd_path, self.cfg_file)
            logging.error(msg)
            raise Exception(msg)

        author_path = self._abs_path('./RegistrationInfo/Author', xmlns)
        author_node = self.xml.find(author_path)
        if author_node is None:
            msg = 'File Format Error: Fail to find "%s" in %s' % (
                author_path, self.cfg_file)
            logging.error(msg)
            raise Exception(msg)

        self.usr_node = usr_node
        self.cmd_node = cmd_node
        self.author_node = author_node
        self.xmlns = xmlns

    @staticmethod
    def _abs_path(path, xmlns):
        """Get absolate path contains XML namespace"""
        return path.replace('/', '/{%(xmlns)s}' % {'xmlns': xmlns})

    @property
    def user(self):
        """
        Get user name of scheduled task
        """
        usr_name = self.usr_node.text.strip()
        logging.debug('Get User name %s', usr_name)
        return usr_name

    @user.setter
    def user(self, usr_name):
        """Set user name of scheduled task"""
        logging.debug('Set User name to %s', usr_name)
        usr_name = usr_name.strip()
        if usr_name == self.user:
            return
        self.usr_node.text = usr_name
        self._saved = False

    @property
    def command(self):
        """Get command line of scheduled task"""
        cmd = self.cmd_node.text.strip()
        logging.debug('Get Command: %s', cmd)
        return cmd

    @command.setter
    def command(self, cmd):
        """Set command line of schedule task"""
        logging.debug('Set task command name to %s', cmd)
        cmd = cmd.strip()
        if cmd == self.command:
            return

        self.cmd_node.text = cmd
        self._saved = False

    @property
    def author(self):
        """Get author of scheduled task"""
        auth = self.author_node.text.strip()
        logging.debug('Get task author: %s', auth)
        return auth

    @author.setter
    def author(self, author):
        """Set author of scheduled task"""
        logging.debug('Set task author to %s', author)
        usr_name = author.strip()
        if usr_name == self.author:
            return

        self.author_node.text = usr_name
        self.user = usr_name
        self._saved = False

    def sync(self):
        """Save configuration settings to XML file"""
        if self._saved:
            logging.debug('%s closed w/o modification', self.cfg_file)
            return

        content = ElementTree.tostring(self.xml.getroot())
        logging.debug('Update XML file: %s', self.cfg_file)
        with open(self.cfg_file, 'w') as xmlfile:
            xmlfile.truncate()
            xmlfile.write(content)

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.sync()
        ElementTree.register_namespace('', '')

    @staticmethod
    def gen_xml(usr, cmd):
        """Generate XML configuration file for scheduled task"""
        return _TASK_CFG_TEMPLATE % {'user': usr, 'command': cmd}

    @staticmethod
    def create_task(name, cfg_file):
        """Create scheduled task"""
        Shell.system('%s /create /tn %s /XML "%s" /F' %
                     (SCHTA
         SCHTASKS_CMD, name, cfg_file))
