## About Mr. Hide##

Mr. Hide is a light weight static web site generator capable for maintaining individual 
blog with support of pages and tags. It generates posts by year, month, tag with pages, and plain pages.
Also it generates sitemap, rss feeds and site.yaml for Google App Engine hosting. 
You will have your _source_ folder with all css, images and scripts together with _post_ files. A post file must have extension *.md*
and contain the following format:
    title : My Post Title
	date  : 01/12/2010
	text:
	[Formatted post contents]

The __date__ format is controlled by `--use24hours` options (True by default) and can be one of the following:

- `%d/%m/%Y` _Date only_
- `%d.%m.%Y`
- `%d.%m.%Y, %I.%M %p` _Date and time with AM/PM strings_
- `%d/%m/%Y, %I/%M %p`
- `%d.%m.%Y, %H.%M` _Date and time in 24 hours format_
- `%d/%m/%Y, %H/%M`

The post content is read from the next line after _text_ section is found. Text read from section is
a some sort of *kown* format, with markdown suggested by default but anything like Textile or BBCode can be used.

##Installation##

Simply clone Mr.Hide and install with setup.py
    git clone git://github.com/AwesomeStanly/MrHide.git mrhide
    cd mrhide
    sudo python setup.py install

Dependences with default features:

- Mako >= 0.2.5
- markdown >= 2.0

Optional:

- unidecode >= 0.04 (git clone http://code.zemanta.com/tsolc/git/unidecode)


## How Mr. Hide works ##

Your website is represented by a number of files used by Mr. Hide to generate html pages, robots.txt, rrs feeds and 
other things. The markup of generated html is controlled by templates. Template engine is Mako by default
by Mr. Hide is easily configurable even on source level, so feel free to embed anything to _helpers_ module and use them.
So Basically you store you blog content & media somewhere safe up in clouds, like your GitHub or DotMac or Amazon. When
you want to publish a new post or edit existing or just update your markup, you need to call Mr.Hide to generate html for
you. Then you sync your changes to remote host or update your local http server for debugging. Automation of it is fairly
trivial. Should be something like:

    #!/bin/bash
    cd src/mysite
    mrhide --source . --target /var/www/myblog --root /myblog
    scp -r /var/www/myblog/* me@server.com:/var/www/production/myblog/
    ssh me@server.com sh /etc/init.d/nginx reload

##Blog Generation##

There are *three* expected templates to be found by generator of html. The
templates are rendered with the following arguments available at generation time:
####post.mako####

Template for single post entry. It should host whatever commenting system you'd like. Discuss works fine, but pretty anything should work.

- _dict_ *post* - The dictionary with post data
  Post dictionary keys:
- _unicode_ *title* - The title
- _datetime_ *date* - Published date
- _list_ *text* - List of unicode strings with post content

####page.mako####

Template for a single page with posts.

- _list_ *page* - List of dictionaries with posts of the page. See post.mako
- _int_ *pageNumber* - Current page number
- _int_ *totalPages* - Total pages to go
- _dict_ *filters* - Filters dict if any or empty dict. Filters may by tags, or date or something else. Item key is a filter name, value is a filter argument. Example: filters : { 'tag' : 'SomeTag' , 'year' : '2008' }. 

####index.mako####

Template for blog index page with summary of posts & tags.

- _list_ __posts__ - All posts
- _list_ __tags__ - All tags
- _dict_ __dates__ - Posts in year/month/day dicts
- _list_ __monthsByPosts__ - List of months with posts

The structure of expected _source_ folder:
    MyBlog
    |-posts/*.md		(Each file is a post with title & date. Use text editor of your choice :)
    |-resources/*		(Put your css, js, images and other stuff you may need in template markup)
    |-templates/*.mako	(You actual markup files. Index page, Post template & Page template)

##Site Generation##

In order to build misc site pages you need to place templates for each page into _posts_ folder. Each generated page will be places in a separate
folder with name equal to it's template file name without extension.

##Helpers##

In order to have links to resources and generated html pages consistent and correct you need to
use provided *helpers*. The *helpers* module may import any other tool useful for you. It provides
to following methods _recommended_ for use:

- format_timestamp(datetime) Returns string with neat datetime format readable for humans
- resource('path/to/res') Builds a path something you put in resources
- link('path/to/page') Builds a path to generated html page. You should specify paths according to *generated layout* (See below)
- cut(text, index)  If specified index is good to break(See shouldBreak) returns text cutted at index. Otherwise scans for first good to break index before specified in reversed order. Useful to create "read more..." links.

## Generated Layout ##

The generated html, resources, rss feeds layout.

- /sitemap.xml
- /index.html
- /page/[num]/index.html
- /post/index.html -> /post/1/index.html
- /post/id/[id]/index.html
- /post/date/[year]/[month]/[day]/index.html
- /post/date/[year]/[month]/index.html ( index is generated for each __monthsByPosts__ argument in _index.mako_ )
- /post/feed.rss
- /tag/[name]/[pageNumber]/index.html
- /tag/[name]/index.html -> /tag/[name]/1/index.html
- /tag/[name]/feed.rss
- /[misc-page-1]/index.html
- /[misc-page-2]/index.html
- /[misc-page-3]/index.html

Static resources for templates used in markup
- %source/{defines.inResources} -> %target/{defines.resources}

## Configurable defaults ##

Values of expected folders for both source & target layout is controlled by
*defines* module. You can override the following things:

### Output settings ###

- `resources = 'res'` _path to generated resources folder inside target_
- `posts = 'post'` _path to generated post inside target_
- `pages = 'page'` _path to generated pages inside target_
- `tags = 'tag'` _path to generated tags inside target_

### Input settings ###

- `inResources = 'resources'` _path to input resources folder inside source_
- `inPosts = 'posts'` _path to input post files inside source_
- `inTemplates = 'templates'` _path to input templates inside source_

- `inPages = 'pages'` _path to input misc page templates inside source_

### Template per category of generated pages ###

- `postTemplate = 'post.mako'` _name of template for single post_
- `pageTemplate = 'page.mako'` _name of template for single page_
- `indexTemplate = 'index.mako'` _name of template for summary page_

## Usage ###
Generate a site to `/var/wwwroot/blog` from posts & markup at `/home/user/mycoolblog`. The __web root__ will be `/blog`. That means that `/var/wwwroot` is your **site http server** root path) and **public url** is `http://website.com/`.The result path of deployed website will be `http://website.com/blog`

    mrhide --source /home/user/mycoolblog --target /var/www/root/blog --url http://website.com --webroot /blog --name MySite

Optionally add `--clear` to remove target before generation and/or `--debug` to enable debug output. Type `mrhide --help` for full list of options.

##License##

Mr. Hide is under cc by-nc-sa license.

###Attribution Non-Commercial Share Alike###

This license lets others remix, tweak, and build upon your work non-commercially, as long as they credit you and license their new creations under the identical terms. Others can download and redistribute your work just like the by-nc-nd license, but they can also translate, make remixes, and produce new stories based on your work. All new work based on yours will carry the same license, so any derivatives will also be non-commercial in nature.