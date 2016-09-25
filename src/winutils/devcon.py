# encoding=utf-8
import logging

from ctypes import *
cfg = windll.cfgmgr32
adv = windll.Advapi32


CM_DRP_DEVICEDESC = 0x00000001
CM_DRP_HARDWAREID = 0x00000002
CM_DRP_COMPATIBLEIDS = 0x00000003
CM_DRP_UNUSED0 = 0x00000004
CM_DRP_SERVICE = 0x00000005
CM_DRP_CLASS = 0x00000008
CM_DRP_CLASSGUID = 0x00000009
CM_DRP_DRIVER = 0x0000000A
CM_DRP_CONFIGFLAGS = 0x0000000B
CM_DRP_MFG = 0x0000000C
CM_DRP_FRIENDLYNAME = 0x0000000D


NULL = 0

class Device(object):
    CRVALS = {
        0x00000000:"CR_SUCCESS",
        0x00000001:"CR_DEFAULT",
        0x00000002:"CR_OUT_OF_MEMORY",
        0x00000003:"CR_INVALID_POINTER",
        0x00000004:"CR_INVALID_FLAG",
        0x00000005:"CR_INVALID_DEVNODE",
        0x00000006:"CR_INVALID_RES_DES",
        0x00000007:"CR_INVALID_LOG_CONF",
        0x00000008:"CR_INVALID_ARBITRATOR",
        0x00000009:"CR_INVALID_NODELIST",
        0x0000000A:"CR_DEVNODE_HAS_REQS",
        0x0000000B:"CR_INVALID_RESOURCEID",
        0x0000000C:"CR_DLVXD_NOT_FOUND",
        0x0000000D:"CR_NO_SUCH_DEVNODE",
        0x0000000E:"CR_NO_MORE_LOG_CONF",
        0x0000000F:"CR_NO_MORE_RES_DES",
        0x00000010:"CR_ALREADY_SUCH_DEVNODE",
        0x00000011:"CR_INVALID_RANGE_LIST",
        0x00000012:"CR_INVALID_RANGE",
        0x00000013:"CR_FAILURE",
        0x00000014:"CR_NO_SUCH_LOGICAL_DEV",
        0x00000015:"CR_CREATE_BLOCKED",
        0x00000016:"CR_NOT_SYSTEM_VM",
        0x00000017:"CR_REMOVE_VETOED",
        0x00000018:"CR_APM_VETOED",
        0x00000019:"CR_INVALID_LOAD_TYPE",
        0x0000001A:"CR_BUFFER_SMALL",
        0x0000001B:"CR_NO_ARBITRATOR",
        0x0000001C:"CR_NO_REGISTRY_HANDLE",
        0x0000001D:"CR_REGISTRY_ERROR",
        0x0000001E:"CR_INVALID_DEVICE_ID",
        0x0000001F:"CR_INVALID_DATA",
        0x00000020:"CR_INVALID_API",
        0x00000021:"CR_DEVLOADER_NOT_READY",
        0x00000022:"CR_NEED_RESTART",
        0x00000023:"CR_NO_MORE_HW_PROFILES",
        0x00000024:"CR_DEVICE_NOT_THERE",
        0x00000025:"CR_NO_SUCH_VALUE",
        0x00000026:"CR_WRONG_TYPE",
        0x00000027:"CR_INVALID_PRIORITY",
        0x00000028:"CR_NOT_DISABLEABLE",
        0x00000029:"CR_FREE_RESOURCES",
        0x0000002A:"CR_QUERY_VETOED",
        0x0000002B:"CR_CANT_SHARE_IRQ",
        0x0000002C:"CR_NO_DEPENDENT",
        0x0000002D:"CR_SAME_RESOURCES",
        0x0000002E:"CR_NO_SUCH_REGISTRY_KEY",
        0x0000002F:"CR_INVALID_MACHINENAME",
        0x00000030:"CR_REMOTE_COMM_FAILURE",
        0x00000031:"CR_MACHINE_UNAVAILABLE",
        0x00000032:"CR_NO_CM_SERVICES",
        0x00000033:"CR_ACCESS_DENIED",
        0x00000034:"CR_CALL_NOT_IMPLEMENTED",
        0x00000035:"CR_INVALID_PROPERTY",
        0x00000036:"CR_DEVICE_INTERFACE_ACTIVE",
        0x00000037:"CR_NO_SUCH_DEVICE_INTERFACE",
        0x00000038:"CR_INVALID_REFERENCE_STRING",
        0x00000039:"CR_INVALID_CONFLICT_LIST",
        0x0000003A:"CR_INVALID_INDEX",
        0x0000003B:"CR_INVALID_STRUCTURE_SIZE",
        0x0000003C:"NUM_CR_RESULTS"
    }


    def __init__(self, devInst):
        self.devInst = devInst
        logging.debug('device instace handle: %s' % self.devInst)


    @property
    def id(self):
        buf  = (c_wchar*1024)()
        blen = c_int(1024)
        cr   = cfg.CM_Get_Device_IDW(self.devInst, buf, byref(blen), 0)
        if cr == 0:
            return buf.value
        else:
            logging.debug('Failed to get device id: %s' % self.get_err(cr))
            return None


    @property
    def hwid(self):
        return self.get_prop(CM_DRP_HARDWAREID)


    @property
    def Description(self):
        return self.get_prop(CM_DRP_DEVICEDESC)


    @property
    def Class(self):
        return self.get_prop(CM_DRP_CLASS)


    @property
    def Manufacturer(self):
        return self.get_prop(CM_DRP_MFG)


    @property
    def CompatibleIds(self):
        ids = self.get_prop(CM_DRP_COMPATIBLEIDS, True)
        if ids is not None and len(ids) > 0:
            return ids.split()
        else:
            return None


    def get_prop(self, prop, mz = False):
        buf  = (c_wchar*1024)()
        blen = c_int(1024)
        cr   = cfg.CM_Get_DevNode_Registry_PropertyW(self.devInst, prop, NULL, buf, byref(blen), 0)
        if cr == 0:
            if not mz:
                return buf.value
            else:
                s = buf[:]
                s = s[:s.find('\x00\x00')]
                s = s.replace("\x00", "\n")
                return s
        else:
            logging.debug('Failed to get property %s: %s' % (prop, self.get_err(cr)))
            return None


    @property
    def childs(self):
        '''Get childs of current device'''
        parent       = c_int(self.devInst)
        devChild     = c_int(0)
        devNextChild = c_int(0)

        if cfg.CM_Get_Child(byref(devChild), parent, 0) == 0:
            # Find first child of current device
            child = Device(devChild.value)
            logging.debug('Child of %s: %s' % (self.devInst, child.Description))

            yield child

            # Find sibling of first child
            while cfg.CM_Get_Sibling(byref(devNextChild), devChild, 0) == 0:
                devChild.value = devNextChild.value

                child = Device(devNextChild.value)
                logging.debug('Child of %s: %s' % (self.devInst, child.Description))
                yield child
        else:
            logging.debug('No childs found for %s' % self.devInst)


    @staticmethod
    def get_root_device():
        '''Get root of device tree'''
        devInst = c_int(0)
        if cfg.CM_Locate_DevNodeW(byref(devInst), 0, 0) == 0:
            return Device(devInst.value)
        else:
            return None


    @classmethod
    def find_device(cls, device_id, flags = 0):
        '''Find device via device id'''
        devInst = c_int(0)

        if device_id is None: device_id = 0
        if device_id != 0:
            device_id = create_unicode_buffer(device_id)

        ret = cfg.CM_Locate_DevNodeW(byref(devInst), device_id, 0)
        if ret == 0:
            return cls(devInst.value)
        else:
            return None


    @classmethod
    def get_err(cls, err_code):
        return cls.CRVALS.get(err_code)



class devcon(object):
    @classmethod
    def find_func(cls, dev, *args):
        if dev.id is not None and dev.id.find(args[0]) == 0:
            return dev

        if dev.hwid is not None and dev.hwid.find(args[0]) ==0:
            return dev

        return None


    @classmethod
    def find(cls, device_id):
        '''Find device via device id or hardware id'''
        root = Device.get_root_device()
        return cls.enum_device(root, cls.find_func, device_id)


    @classmethod
    def enum_device(cls, parent, call_func, *args):
        childs = parent.childs
        if childs is None:
            return None
        else:
            for c in childs:
                ret = call_func(c, *args)
                if ret:
                    return ret
                else:
                    ret = cls.enum_device(c, call_func, *args)

                    if ret:
                        return ret
                    else:
                        continue




if __name__ == '__main__':
    dev = devcon.find(r'PCI\VEN_8086&DEV_10EA&SUBSYS_215317AA&REV_06')
    if dev is None:
        print 'No such device'
    else:
        print dev.Description
