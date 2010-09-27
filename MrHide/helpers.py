#
# Mr. Hide Site Genetator
# Copyright Stanislav Yudin, 2010
#

import os
import sys
import random
import datetime
import base64
import cgi
import urllib
import urlparse
import logging
import defines
import markdown
import string
import logging
from texthlp import cut
from xml.dom.minidom import parseString as parseXmlString

#website root path setup by MrHide.__init__()
webroot = '/'

def link(linkPath):
	if linkPath.startswith('/'):
		linkPath = linkPath[1:]
	return os.path.join(webroot, linkPath)

def resource(resourcePath):
	if resourcePath.startswith('/'):
		resourcePath = resourcePath[1:]
	return os.path.join(webroot, defines.resources, resourcePath)

def format_timestamp(timestamp):
	delta = datetime.datetime.now() - timestamp
	if delta.days > 0:
		if delta.days == 1:
			return '%s day ago on %s' % ( delta.days, timestamp.strftime("%A, %d. %B %Y") )
		else:
			return '%s days ago on %s' % ( delta.days, timestamp.strftime("%A, %d. %B %Y") )
	elif (delta.seconds	 < 3600):
		if (delta.seconds / 60) > 1:
			return '%s minutes ago' % (delta.seconds / 60)
		else:
			return '%s minute ago' % (delta.seconds / 60)
	else:
		return 'on %s ' % timestamp.strftime("%A, %d. %B %Y")
