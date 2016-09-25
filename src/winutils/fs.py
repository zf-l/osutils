# encoding=utf-8
"""
Provide functions to operate file/directory easily.
"""
import os
import time
import re
import subprocess
import logging
import shlex
from shutil import copyfile

from .shell import Shell


def unzip_ps(zip_file, dest_dir):
    """Unzip file to specified directory using PowerShell Command"""
    logging.info('Unzip %s ...', zip_file)

    # Powershell command to unzip file
    cmd = 'powershell.exe -nologo -noprofile -command' + \
          '''"& { Add-Type -A 'System.IO.Compression.FileSystem'; ''' + \
          '''[IO.Compression.ZipFile]::ExtractToDirectory('%s', '%s');}"''' % (zip_file, dest_dir)

    # There is a bug on Win10 ver. 10041 duing unzip progress
    # Exception calling "ExtractToDirectory" with "2" argument(s): "There are no more files."
    # It is a workground to try some times to unzip the file
    i = 0
    desc = ''
    while i < 6:
        logging.info('[%d] : %s', i, cmd)
        prs = subprocess.Popen(cmd, stderr=subprocess.PIPE)
        prs.wait()

        err_msg = prs.stderr.read()
        if len(err_msg) == 0:
            logging.info('unzip completed')
            return True
        else:
            desc = 'Fail to extract file. Error msg: %s' % err_msg
            logging.error(desc)
            i += 1
            time.sleep(10)

    msg = '%s : %s' %(cmd, desc)
    raise Exception(msg)


def _del(file_path):
    '''Delete file using del command'''
    cmd = 'del /f /q "%s"' % file_path

    logging.info('Delete file %s: %s', file_path, cmd)
    ret = os.system(cmd)
    if ret == 0:
        logging.info('File Deleted')
    else:
        msg = 'Cannot delete file. Error code %d' % ret
        logging.error(msg)
        raise Exception(cmd + ',' + msg)


def _rmdir(file_path):
    '''Remove directory using rmdir command'''
    cmd = 'rmdir /s /q "%s"' % file_path

    logging.info('Delete %s: %s', file_path, cmd)
    ret = os.system(cmd)
    if ret == 0:
        logging.info('Directory removed')
    else:
        msg = 'Cannot remove directory. Error code %d' % ret
        logging.error(msg)
        raise Exception(cmd + ',' + msg)


def move(src, dest):
    """Move one file or folder to another direcotry.
    This command can be more effective when move files between the same disk
    """
    cmd = 'move /Y "%s" "%s"' % (src, dest)
    logging.debug('Move %s to %s: %s', src, dest, cmd)
    Shell.system(cmd, shell=True)


def delete(file_path):
    """Delete file/directory even if it is readonly.
    @param file_path: path of file to be deleted.
    """
    if os.path.exists(file_path):
        if os.path.isfile(file_path):
            _del(file_path)
        else:
            _rmdir(file_path)


def copy(src_path, dest_path, **args):
    """copy file or folder to a new path"""
    dir_path = os.path.dirname(dest_path)
    logging.debug('Copy file from %s to %s', src_path, dest_path)

    # Create dir if not exist
    if not is_drive_letter(dir_path):
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    if os.path.isfile(src_path):
        copyfile(src_path, dest_path)
    elif os.path.isdir(src_path):
        copydir(src_path, dest_path, **args)
    else:
        msg = 'Cannot find file: %s' % src_path
        logging.error(msg)
        raise Exception(msg)


def copydir(path, dest, excluded_files=None, log_file=None):
    """Copy directory using robocopy command.
    """
    dest = re.sub(r'([^\\])(\\+)$', r'\1', dest)  # robocopy did not accept directory end with '\'

    logging.info('Copy %s to %s', path, dest)
    command = None

    if log_file is not None:
        log_str = ' >> "%s"' % log_file
    else:
        log_str = ''

    if excluded_files is not None:
        ex_args = _get_exclude_file_args(path, excluded_files)
        if ex_args is not None:
            command = 'robocopy "%s" "%s" %s /mt /e /is' % (path, dest, ex_args)

    if command is None:
        command = 'robocopy "%s" "%s" /mt /e /is' % (path, dest)

    command += log_str
    logging.debug('Command %s', command)

    ret = os.system(command)
    if ret <= 3:
        logging.info('Direcotry copied successfully')
    else:
        msg = 'Failed to copy %s. Error code %d' % (path, ret)
        logging.error(msg)
        raise Exception(msg)


def _get_exclude_file_args(path, excluded_files):
    r"""
    Get arguments for robocopy to exclude some files and direcotrys
    Format: /XF "c:\file1" /XD "c:\folder1" /XD "c:\folder2\folder22" /xf "C:\folder3\file33" /elif
    """
    ex_file = []
    ex_dir = []
    for ex_file in excluded_files:
        rel_path = os.path.join(path, ex_file)

        if not os.path.exists(rel_path):
            logging.warn('Cannot found path: %s', rel_path)
            continue

        if os.path.isfile(rel_path):
            ex_file.append(rel_path)
            logging.debug('Exclude file: %s', rel_path)
        elif os.path.isdir(rel_path):
            ex_dir.append(rel_path)
            logging.debug('Exclude dir: %s', rel_path)

    ex_files = ['/XF "%s"'% i  for i in ex_file]
    ex_dirs = ['/XD "%s"'% i  for i in ex_dir]
    logging.debug('Excude files: %s', str(ex_files))
    logging.debug('Excude dirs : %s', str(ex_dirs))
    ex_file_args = ' '.join(ex_files)
    ex_dir_args = ' '.join(ex_dirs)

    ex_args = ex_file_args
    ex_args = ex_dir_args if len(ex_file_args) == 0 else ex_file_args + ' ' + ex_dir_args

    if len(ex_args) == 0:
        logging.info('No excluded files')
        return None
    else:
        logging.info('Exclued files: %s', ex_args)
        return ex_args


def is_drive_letter(path):
    """Check wheter specified path is a drive letter"""
    return re.match('^[a-zA-Z]{1}:$', path)


def enum_usb_disks():
    r"""
    Get USB Pen drive list
    :return Dist name list like: ['D:', 'E:']
    """
    wmic_cmd = 'wmic'
    cmd = '"%s" logicaldisk where "DriveType=2 and Size<>null" get DeviceID' % wmic_cmd
    cmd_list = shlex.split(cmd)
    cmd_output = subprocess.check_output(cmd_list)
    return re.findall(r'[A-Z]:', cmd_output)


def eject_usb_disk(disk_name):
    """
    Eject USB pen drive
    :param disk_name: USB Drive Name, eg D:, E:
    :return: True, the pen drive has been ejected, else False
    """
    from win32com.client import Dispatch
    from win32com.shell import shell, shellcon

    # Check the disk name is valid or not
    disk_mat = re.match('([a-zA-Z]:)', disk_name)
    if not disk_mat:
        logging.error("USB Pen drive name is not valid: %s", disk_name)
        return False
    disk_name = disk_mat.group(0)

    # Check the specified USB pen drive can be found or not
    if disk_name not in enum_usb_disks():
        logging.info("USB Pen drive not found: %s", disk_name)
        return True

    # Eject the USB Pen drive
    app = Dispatch('Shell.Application')
    disk_obj = app.Namespace(17).ParseName(disk_name)
    disk_obj.InvokeVerb('Eject')
    shell.SHChangeNotify(shellcon.SHCNE_DRIVEREMOVED, shellcon.SHCNF_PATH, disk_name)

    # Check the USB pen drive has been ejected or not
    time.sleep(1)
    if disk_name in enum_usb_disks():
        logging.error("%s has not been ejected", disk_name)
        return False

    return True


def read_unicode_file(file_path):
    """
    Read content from unicode file
    :return: one file object
    """
    import chardet
    import codecs
    file_obj = open(file_path, 'r')
    f_line = file_obj.readline()
    f_enc = chardet.detect(f_line)['encoding']
    logging.debug('encoding:' + f_enc)
    if not f_enc or f_enc.lower() == 'ascii':
        file_obj.seek(0)
        return file_obj
    elif f_enc.lower().startswith('utf-8'):
        file_obj.close()
        return codecs.open(file_path, 'r', f_enc)
    elif f_enc.lower().startswith('utf-16'):
        file_obj.close()
        return codecs.open(file_path, 'r', 'utf_16')
    logging.error('Cannot detect file type')
    return None
