#!/usr/bin/python
#
# MGEN
# Copyright Stanislav Yudin, 2010
#

import os
import sys

try:
	from setuptools import setup, find_packages
except ImportError:
	from ez_setup import use_setuptools
	use_setuptools()
	from setuptools import setup, find_packages

def get_requirements():
	with open("requirements.txt") as f:
		return f.readlines()

DEFAULT_VERSION = '1.0.0'
HASH = os.popen('git rev-parse --short HEAD').read().strip()

try:
	import mgen
	PACKAGE_VERSION = '{0}.{1}.{2}'.format(
		*mgen.__version__)
	BUILD = os.environ.get("BUILD_NUMBER")
	if not BUILD:
		print "Developement build"
		PACKAGE_VERSION = '{0}.git-{1}'.format(PACKAGE_VERSION, HASH)
	else:
		print "Release build"
		PACKAGE_VERSION = '{0}.{1}'.format(PACKAGE_VERSION, BUILD)
	
except:
	print "Warning: Failed to import 'mgen' module. First install?"
	PACKAGE_VERSION = '{0}.git-{1}'.format(DEFAULT_VERSION, HASH)


print "MGEN ver. {0}".format(PACKAGE_VERSION)	

setup(
	name='mgen',
	version=PACKAGE_VERSION,
	description='Lightweight Static Blog Generator',
	author='Stanislav Yudin',
	author_email='decvar@gmail.com',
	url='http://www.endlessinsomnia.com/lab/mrhide.html',
	packages = find_packages(exclude=['ez_setup']),
	include_package_data = True,
	test_suite = 'nose.collector',
	package_data = {'MrHide': ['i18n/*/LC_MESSAGES/*.mo']},
	install_requires  = get_requirements(),
	zip_safe = True,
	scripts = [
		'scripts/mgen',
		'scripts/mgen.cmd'
	]
)
