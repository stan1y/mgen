#
# Mr. Hide Site Genetator
# Copyright Stanislav Yudin, 2010
#

import os
import sys
import random
import datetime
import base64
import hashlib
import cgi
import urllib
import urlparse
import logging
import defines
import markdown
import string
import logging
import BeautifulSoup

from mako import exceptions
from mako.template import Template
from texthlp import cut
from xml.dom.minidom import parseString as parseXmlString

#website root path setup by MrHide.__init__()
webroot = '/'

MonthNames = {
	1 : 'January',
	2 : 'February',
	3 : 'March',
	4 : 'April',
	5 : 'May',
	6 : 'June',
	7 : 'July',
	8 : 'August',
	9 : 'September',
	10 : 'October',
	11 : 'November',
	12 : 'December'
}

def tr(text):
	if not isinstance(text, unicode):
		return text
	try:
		from  unidecode import unidecode
		text = str(unidecode(text))
		return text.replace('\'', '').replace('"', '')
	except ImportError:
		print 'Your text %s has unicode, it can lead to certain problems...' % text
	return text

def urljoin(*args):
	lst = [a.encode('utf-8') for a in args]
	return urllib.quote(os.path.join(*lst))

def link(linkPath):
	if linkPath.startswith('/'):
		linkPath = linkPath[1:]
	#link should be ascii compatible
	hasUnicode = False
	try:
		strLine = str(linkPath)
	except UnicodeEncodeError:
		hasUnicode = True
	
	if hasUnicode:
		linkPath = tr(linkPath)
	
	linkPath = urllib.quote( os.path.join(webroot, linkPath) )	
	return linkPath
	

def resource(resourcePath):
	if resourcePath.startswith('/'):
		resourcePath = resourcePath[1:]
	return os.path.join(webroot, defines.resources, resourcePath)

def format_timestamp(timestamp):
	return 'on %s ' % timestamp.strftime("%A, %d. %B %Y")

def render(content, *args, **kwargs):
  tmpl = Template(content)
  try:
    return tmpl.render(
      encoding = 'utf-8',
      helpers = locals,
      *args,
      **kwargs
    )
  except:
    return exceptions.text_error_template().render()


def text(post, join_with = '\n', *args, **kwargs):
	md_content = markdown.markdown(join_with.join(post['text']))
	return render(md_content, *args, **kwargs)