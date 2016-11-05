#!/usr/bin/python
#
# MGEN Site Genetator
# Copyright Stanislav Yudin, 2010-2012
#

import os
import sys
import yaml
import logging
from logging.handlers import TimedRotatingFileHandler


# MGEN package version
__version__ = (3, 0, 0)


# Paths to look for options file, in order
__options_paths__ = ['./mgen.conf', '~/.mgen/mgen.conf', '/etc/mgen/mgen.conf']


# Options key constants
SLUGS_LOCAL_PATH = "slugs_local_path"
THEMES_PATH = "themes_path"


# Global shared options dict with defaults
__options__ = {
    SLUGS_LOCAL_PATH: "/tmp/mgen/slugs",
    THEMES_PATH: "/usr/local/share/mgen/themes"
}


log = logging.getLogger(__name__)


def options(key=None):
    '''Get shared options'''
    global __options__
    if key is None:
        return __options__
    else:
        return __options__.get(key, None)


def read_options():
    global __options_paths__
    global __options__
    for options_path in __options_paths__:
        if os.path.exists(options_path):
            log.debug('reading options from "%s"' % options_path)
            with open(options_path, 'r') as options_file:
                opts = yaml.load(options_file)
                for key in opts:
                  if getattr(__options__, key) == None:
                    setattr(__options__, key, opts[key])


#
# MGEN Logging Subsystem
#


class MGENRotatingFileHandler(TimedRotatingFileHandler):
    def _prevent_fd_inheritance(self):
        fd = self.stream.fileno()
        if sys.platform == 'win32':
            import win32api
            import win32con
            import msvcrt
            fd = msvcrt.get_osfhandle(fd)  # required only for file
            win32api.SetHandleInformation(fd, win32con.HANDLE_FLAG_INHERIT, 0)
        else:
            import fcntl
            old_flags = fcntl.fcntl(fd, fcntl.F_GETFD)
            fcntl.fcntl(fd, fcntl.F_SETFD, old_flags | fcntl.FD_CLOEXEC)

    def __init__(self, **kwargs):
        super(MGENRotatingFileHandler, self).__init__(**kwargs)
        self._prevent_fd_inheritance()
        
    def doRollover(self):
        super(MGENRotatingFileHandler, self).doRollover()
        self._prevent_fd_inheritance()  # to be on the safe side if the first rotation occurs before the child start
        # here cah be added gzip thread


def configure_log(filename,
                  debug = True,
                  console = True,
                  format = '%(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] %(message)s',
                  dateformat = '%d/%m/%y %H:%M:%S'):
    """configure global handlers for logging module"""
    root = logging.getLogger()
    root.handlers = []
    if debug:
        root.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.INFO)
    formatter = logging.Formatter(format, dateformat)
    
    rh = MGENRotatingFileHandler(when='midnight', interval=1, backupCount=5, utc=True, filename=filename)
    rh.setFormatter(formatter)
    root.addHandler(rh)
    
    if console:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        root.addHandler(ch)
    