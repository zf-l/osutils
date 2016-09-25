# encoding=utf-8
"""Access share drive from Windows OS"""
import os
import time
import re
import logging

from .fs import copy, delete
from .shell import NET_CMD


class ShareDrive(object):
    r"""Class to mount/umount Common Internet File System

    >>> ShareDrive.is_valid_path(r'\\david-pc\test')
    True
    >>> ShareDrive.is_valid_path(r'https://www.baidu.com')
    False
    """
    path_pattern = re.compile(r'\\\\[^\\]+')

    def __init__(self, path=None, usr=None, pwd=None):
        self._path = path
        self.usr = usr
        self.pwd = pwd

    def __enter__(self):
        if self._path is not None:
            self.open(self._path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self, path=None, device=''):
        r"""Mount specified share drive
        @param path: Remote folder path like: \\david-pc\share
        """
        if path:
            self._path = path
        else:
            path = self._path

        if self.usr:
            _mount_cmd = '%s use %s "%s" /user:%s "%s"'
            cmd = _mount_cmd % (NET_CMD, device, path, self.usr, self.pwd)
        else:
            cmd = '%s use %s "%s"' % (NET_CMD, device, path)

        logging.info('Mount share drive(%s)', path)
        logging.debug(cmd)

        # Invoke command to mount share drive
        ret = os.system(cmd)
        if ret == 0:
            logging.info('Mounted')
            return path
        else:
            logging.error('Share drive cannot be mounted. Error code %d', ret)
            return None

    def download(self, rmt_path, loc_path):
        """
        Download file from share drive to local file system.
        @param rmt_path: Remote file path
        @param loc_path: Local file path
        """
        if not self.exists(rmt_path):
            logging.error("%s does not exist", rmt_path)
            return False
        rmt_path = self.get_abs_path(rmt_path)
        return copy(rmt_path, loc_path)

    def upload(self, loc_path, rmt_path):
        """Upload file/ to share folder
        @param loc_path: Local file/folder path
        @param rmt_path: Remote file/folder path
        @return: True if successed else False
        """
        rmt_path = self.get_abs_path(rmt_path)
        if not delete(rmt_path):
            logging.error("Failed to upload file")
            return False
        else:
            return copy(loc_path, rmt_path)

    def is_file(self, remote_path):
        """
        Check whether remote path is a file path
        """
        remote_path = self.get_abs_path(remote_path)
        return os.path.isfile(remote_path)

    def is_dir(self, remote_path):
        """
        Check whether remote path is a folder path
        """
        remote_path = self.get_abs_path(remote_path)
        return os.path.isdir(remote_path)

    def exists(self, path, retry_count=50, delay=0.5):
        """
        Check whether remote path exists or not
        """
        path = self.get_abs_path(path)
        # Workaround for window share drive
        # Sometimes, windows share drive cannot be detected.
        # Wait about 6 seconds, the path can be accessed.
        for i in range(retry_count):
            logging.debug('%d try to detect file', i)
            if os.path.exists(path):
                return True
            time.sleep(delay)

        return False

    def delete(self, path):
        """
        Delete file from share folder
        """
        path = self.get_abs_path(path)
        return delete(path)

    def mkdir(self, path):
        """
        Create directory on share folder
        """
        path = self.get_abs_path(path)
        os.makedirs(path)

    def close(self):
        """
        Close connection
        """
        command = '%s use "%s" /delete' % (NET_CMD, self._path)
        logging.debug('Share drive will be umounted. Command: %s', command)
        os.system(command)

    def get_abs_path(self, path):
        """
        Get the absolute path
        """
        if not self.is_valid_path(path):
            return os.path.join(self._path, path)
        return path

    @classmethod
    def is_valid_path(cls, path):
        """Check whether given path is a valid share drive path"""
        return re.match(cls.path_pattern, path) is not None


if __name__ == '__main__':
    # import doctest
    # doctest.testmod()
    with ShareDrive(r'\\shwdejointd140\reports\temp') as cd:
        print cd.delete("LogsKnownPatterns.log")
        print cd.delete("temp2")

