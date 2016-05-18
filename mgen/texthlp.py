#
# Mr. Hide Site Genetator
# Copyright Stanislav Yudin, 2010
#

import string
import logging

def shoudBreak(char):
	return (char in string.whitespace) or (char in ['.', '!', '?', ',', ';'])
	
def isTagStart(char):
	return char == '<'

def isTagEnd(char):
	return char == '>'
	
def inTag(text, index):
	startFound = False
	endFound = False
	startAt = 0
	endAt = 0
	if text[index] in ['<', '>']:
		return False, 0, 0
	
	for delta in xrange(1, len(text) - index):
		if not endFound and index + delta < len(text) and isTagEnd(text[index + delta]):
			endFound = True
			endAt = index + delta
			logging.debug('found +%d : %s' % (delta, text[index + delta]))

		if not startFound and index - delta >= 0 and isTagStart(text[index - delta]):
			startFound = True
			startAt = index - delta
			logging.debug('found -%d : %s' % (delta, text[index - delta]))
		
		if (startFound and endFound):
			logging.debug('found tag <%d,%d>' % (startAt, endAt))
			return (startFound and endFound), startAt, endAt

	return False, 0, 0
	
	
### cut processing ###
	
def cut(text, lenght):
	#too small
	if len(text) <= lenght:
		return text
		
	#scan text
	
	isInTag, tagStart, tagEnd = inTag(text, lenght)
	if isInTag:
		if tagStart > 1 :
			return text[:tagStart - 1]
		else:
			return text[:tagEnd + 1]
	else:
		for index in reversed(range(0, lenght - 1)):
			if shoudBreak(text[index]):
				return text[:index]
		
	#no sutable place found, return all
	return text