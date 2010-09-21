#!/usr/bin/python
import os
import sys
import logging
import optparse
import MrHide

__debug = False

if __name__ == '__main__':
	parser = optparse.OptionParser()
	
	parser.add_option("--debug", action="store_true", default=False, help="Enable debug outout")
	parser.add_option("-s", "--source", help = "Path to blog posts")
	parser.add_option("-t", "--target", help = "Path where to put results")
	parser.add_option("-p", "--posts", help = "Number of posts per page", default = 10)
	parser.add_option("-r", "--webroot", help = "Root path of deployed website.", default = "/")
	
	parser.add_option("--clear", action="store_true", default=False, help="Remove target if any.")
	
	parser.add_option("--skip-posts", action="store_true", default=False, help="Do not generate posts.")
	parser.add_option("--skip-pages", action="store_true", default=False, help="Do not generate pages.")
	parser.add_option("--skip-tags", action="store_true", default=False, help="Do not generate tags.")
	parser.add_option("--skip-rss", action="store_true", default=False, help="Do not generate rss feeds.")
	parser.add_option("--skip-resources", action="store_true", default=False, help="Do not generate resources & scripts.")
	parser.add_option("--skip-indexes", action="store_true", default=False, help="Do not generate index files.")
	
	(options, args) = parser.parse_args()

	#logging configuration
	if options.debug:
		print 'DEBUG mode is ON'
	
	if options.source and os.path.exists(options.source) and options.target:
		if os.path.exists(options.target) and options.clear:
			os.system('rm -fr %s' % options.target)
			
		hide = MrHide.MrHide(options)
		hide.Generate()
	else:
		parser.print_help()
