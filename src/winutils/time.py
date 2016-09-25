#encoding=utf-8
"""
Define date time related funcitons
"""
import re
import subprocess

class Timezone(object):
    """Define class to store timezone settings"""
    def __init__(self, utc_offset, display_name, time_zone_id):
        self.utc_offset = utc_offset
        self.display_name = display_name
        self.time_zone_id = time_zone_id

    @classmethod
    def list_timezone(cls):
        """Lists all valid time zone IDs and display names"""
        cmd = 'tzutil /l'
        cmd_output = subprocess.check_output(cmd)

        name_pattern = \
            re.compile(r'\((?P<utc_offset>UTC[\+\-]\d{2}:\d{2})\)\s+(?P<display_name>.*)')

        timezones = []
        latest_obj = None
        for line in cmd_output.split('\n'):
            name_mat = name_pattern.match(line)
            if name_mat:
                latest_obj = cls(name_mat.group('utc_offset'), name_mat.group('display_name'), None)
            elif latest_obj:
                latest_obj.time_zone_id = line
                timezones.append(latest_obj)
                latest_obj = None

        return timezones

    @staticmethod
    def current_tz_id():
        """Get current timezone ID"""
        return subprocess.check_output('tzutil /g').strip()

    @staticmethod
    def set_timezone(timezone_id):
        """Set timezone to specified value"""
        return subprocess.check_call('tzutil /s "%s"' % timezone_id) == 0


def set_date(year, month, day):
    """Set date of current OS using date command"""
    set_cmd = 'date %s/%s/%s' % (month, day, year)
    return subprocess.check_call(set_cmd, shell=True) == 0


if __name__ == '__main__':
    # for tz in Timezone.list_timezone():
    #     print tz.utc_offset
    #     print tz.display_name
    #     print tz.time_zone_id
    print Timezone.current_tz_id()
