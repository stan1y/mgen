#!/usr/bin/python
#
# Mr. Hide Site Genetator
# Copyright Stanislav Yudin, 2010-2012
#

import os
import sys
import logging
import datetime
import optparse
import MrHide

__debug = False

if __name__ == '__main__':
    parser = optparse.OptionParser()
    
    parser.add_option("--debug", action="store_true", default=False, help="Enable debug output.")
    parser.add_option("-s", "--source", help = "Path to your blog source.")
    parser.add_option("-t", "--target", help = "Path for output.")
    parser.add_option("-n", "--name", help = "Website name")
    parser.add_option("-u", "--url", help = "An external wellformed url to deployed website, excluding webroot. Default is 'localhost'", default = 'localhost')
    parser.add_option("-r", "--webroot", help = "Root path of deployed website. Used for links & resources. Default is '/'", default = "/")
    parser.add_option("--posts", help = "Number of posts per page. Default is 10.", default = 10)
    parser.add_option("--items", help = "Number of items per rss feed. Default is 50.", default = 30)
    parser.add_option("--title", help = "Title your of generated rss feeds. Default is capitalized source folder name.")
    parser.add_option("--years", help = "Values list separated by comma for inital years filter. Default is current year only")
    parser.add_option("--lang", help = "Language of your site. Default is 'en'", default = 'en')
    parser.add_option("--use24hours", help = "All time values are read and written with format '%%H:%%M', otherwise as '%%I:%%M %%p. Default is True.' ", action="store_true", default=True)
    parser.add_option("--transliterate", action="store_true", help = "Convert unicode in post id to transliterated version. Requries 'unidecode'", default = True)
    
    parser.add_option("--clear", action="store_true", default=False, help="Remove target if any.")
    
    parser.add_option("--skip-posts", action="store_true", default=False, help="Do not generate posts.")
    parser.add_option("--skip-pages", action="store_true", default=False, help="Do not generate pages.")
    parser.add_option("--skip-tags", action="store_true", default=False, help="Do not generate tags.")
    parser.add_option("--skip-rss", action="store_true", default=False, help="Do not generate rss feeds.")
    parser.add_option("--skip-resources", action="store_true", default=False, help="Do not generate resources & scripts.")
    parser.add_option("--skip-indexes", action="store_true", default=False, help="Do not generate index files.")
    parser.add_option("--skip-sitemap", action="store_true", default=False, help="Do not generate blog site map.")
    parser.add_option("--skip-misc", action="store_true", default=False, help="Do not generate misc pages.")
    parser.add_option("--skip-gae", action="store_true", default=False, help="Do not generate GAE site.yaml.")
    
    (options, args) = parser.parse_args()

    #logging configuration
    if options.debug:
        print 'DEBUG mode is ON'
        
    if options.years:
        options.years = [int(y.strip()) for y in options.years.split(',')]
    else:
        options.years = [ datetime.datetime.now().year ]
    
    if options.source and os.path.exists(options.source) and options.target and options.url:
        if os.path.exists(options.target) and options.clear:
            for path in os.listdir(options.target):
                if not path.startswith('.'):
                    os.system('rm -fr %s' % os.path.join(options.target, path))
        
        #default title for site
        if not options.title:
            source = os.path.abspath(options.source)
            if source.endswith('/'):
                source = source[:1]
            options.title = os.path.basename(source).capitalize()
        
        hide = MrHide.MrHide(options)
        hide.Generate()
    else:
        parser.print_help()
