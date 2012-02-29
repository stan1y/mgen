#!/usr/bin/python
#
# Mr. Hide Site Genetator
# Copyright Stanislav Yudin, 2010
#

try:
	from setuptools import setup, find_packages
except ImportError:
	from ez_setup import use_setuptools
	use_setuptools()
	from setuptools import setup, find_packages

setup(
	name='mrhide',
	version='0.0.3',
	description='Lightweight Static Blog Generator',
	author='Stanislav Yudin',
	author_email='decvar@gmail.com',
	url='http://www.endlessinsomnia.com/lab/mrhide.html',
	install_requires=[
		"Mako>=0.2.5",
		"markdown>=2.0"
	],
	packages = find_packages(exclude=['ez_setup']),
	include_package_data = True,
	test_suite = 'nose.collector',
	package_data = {'MrHide': ['i18n/*/LC_MESSAGES/*.mo']},
	zip_safe = True,
	scripts = ['scripts/mrhide']
)
