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
from xml.dom.minidom import parseString as parseXmlString

#website root path setup by MrHide.__init__()
webroot = '/'

def shoudBreak(text):
	return (text in string.whitespace) or (text in ['.', '!', '?', ',', ';'])

def cut(text, lenght):
	#too small
	if len(text) <= lenght:
		return text
	
	if shoudBreak(text[lenght - 1]):
		return text[:lenght - 1]
	else:
		for index in reversed(range(0, lenght - 1)):
			if shoudBreak(text[index]):
				return text[:index]
				
		#no sutable place found, return all
		return text

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
			return '%s day ago on %s' % ( delta.days, timestamp.strftime("%A, %d. %B %Y %I:%M%p") )
		else:
			return '%s days ago on %s' % ( delta.days, timestamp.strftime("%A, %d. %B %Y %I:%M%p") )
	elif (delta.seconds	 < 3600):
		if (delta.seconds / 60) > 1:
			return '%s minutes ago' % (delta.seconds / 60)
		else:
			return '%s minute ago' % (delta.seconds / 60)
	else:
		return 'on %s ' % timestamp.strftime("%A, %d. %B %Y %I:%M%p")
