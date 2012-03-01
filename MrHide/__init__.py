#
# Mr. Hide Site Genetator
# Copyright Stanislav Yudin, 2010
#

__version__ = '0.0.3'

import sys
import os
import urllib
import logging
import datetime

from mako.template import Template
from mako.lookup import TemplateLookup

import helpers
import defines

def yesno(b):
	if b: 
		return 'yes'
	else: 
		return 'no'

class Post(dict):
	#sorting with date member for list.sort()
	def __cmp__(self, other):
		if self['date'] == other['date']: return 0
		if self['date'] < other['date']: return -1
		else: return 1


# RSS Feed template 
# Arguments:
#  string title - options.title
#  string url - options.url
#  string desc - a description
#  string lang - a lang value {en, de, es, etc}
#  list posts
# Arguments for item rendering:
#  helpers & os modules
#  int cut_at - options.cut_at
#  string webRoot - options.webroot
#  dict postSizes - dictioanry with size of each post html, key is post['id']

rssTemplate = '''# -*- encoding:utf-8 -*-
<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
   <channel>
	  <title>${title}</title>
	  <link>${url}</link>
	  <description>${desc}</description>
	  <language>${lang}</language>
		%for post in posts:
			<% postSize = postSizes[post['id']] %>
			<item>
				<title>${post['title']}</title>
				<pubDate>${post['date'].isoformat()}</pubDate>
				<description>${helpers.cgi.escape(helpers.markdown.markdown(helpers.cut(''.join(post['text']), cut_at)))}</description>
				<enclosure
					url="${url + webRoot + '/' + post['id']}"
					type="text/html"
					length="${postSize}" />
			</item>
		%endfor
   </channel>
</rss>
'''

# Sitemap template
#
# Arguments:
#  list posts - All posts
#  list pages - All pages
#  dict tags - All tags
#  list years - options.years
#  string url - options.url
#  string webRoot - options.webroot
siteMapTemplate = '''# -*- encoding:utf-8 -*-
<?xml version='1.0' encoding='UTF-8'?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
			    http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
	%for post in posts:
		<url>
			<loc>${url + webRoot + '/post/id/' + post['id']}</loc>
		</url>
	%endfor
	
	%for y in dates:
		%for m in dates[y]:
			%if dates[y][m]:
				%for d in dates[y][m]:
					%if d:
						%for post in dates[y][m][d]:			
							<url>
								<loc>${url + webRoot + '/post/date/%d/%d/%d/index.html' % (y, m, d)}</loc>
							</url>
						%endfor
					%endif
				%endfor
			%endif
		%endfor
	%endfor

	%for pageIndex in range(1, len(pages)):
		<url>
			<loc>${url + webRoot + '/page/' + str(pageIndex)}</loc>
		</url>
	%endfor
	
	%for tag in tags.keys():
		<url>
			<loc>${url + webRoot + '/tag/' + tag}</loc>
		</url>
	%endfor
	
</urlset>
'''

class MrHide(object):
	def __init__(self, options):
		if options.debug:
			logging.basicConfig(level = logging.DEBUG)

		self.options = options	
		
		helpers.webroot = options.webroot
		
		print 'Mr.Hide ver. %s' % __version__
		print 'Building web blog for:'
		print ' %s [%s]' % ( options.title, options.url + options.webroot )
		print 'Source			: %s' % options.source
		print 'Output			: %s' % options.target
		print 'Webroot			: %s' % options.webroot
		print 'Geneator Options'
		print 'Transliteration	: %s' % yesno( options.transliterate )
		print 'Use 24 hours		: %s' % yesno( options.use24hours )
		print 'Years filter		: %s' % ','.join([str(y) for y in options.years])
		print 'Posts per page		: %d' % options.posts
		print 'Items per channel	: %d' % options.items
		print 'Pages			: %s' % yesno( not options.skip_pages)
		print 'Posts			: %s' % yesno( not options.skip_posts )
		print 'Pages			: %s' % yesno( not options.skip_pages)
		print 'Tags			: %s' % yesno( not options.skip_tags)
		print 'Resources		: %s' % yesno( not options.skip_tags)
		
		self.tagsMap = {}
		self.pagesMap = {}
		self.templates = TemplateLookup(directories=[ os.path.join(self.options.source, defines.inTemplates) ],
										output_encoding='utf-8',
										encoding_errors='replace')
		
	#Define how Hide will read with post data
	allowed_sections = ['title', 'date', 'tags', 'text']
	def title(self, post, value):
		post['title'] = value
		
	def date(self, post, value):
		#we got a number of ways how to define a date
		#it can be '%d.%m.%Y' or '%d/%m/%Y' and optionally
		#both can have a ', %H.%M [%p]' suffix
		value = value.strip()
		timeFmt = ''
		dateFmt = ''
		
		 
		if '/' in value:
			d = '/'
			dateFmt = '%d/%m/%Y'
		elif '.' in value: 
			d = '.'
			dateFmt = '%d.%m.%Y'
		else:
			dateFmt = ''
			
		if dateFmt:	
			if not self.options.use24hours: 
				timeFmt = ', %I.%M %p'
			elif ',' in value: 
				timeFmt = ', %H.%M'
			
		post['date'] = datetime.datetime.strptime(value.strip(), '%s%s' % (dateFmt, timeFmt))
		
	def tags(self, post, value):
		post['tags'] = [ tag.strip() for tag in value.split(',') if tag]
		
	def text(self, post, value):
		post['text'] = []
	
	def ParsePost(self, filename):
		logging.debug('Parsing %s' % filename)
		post = Post()
		with open(filename, 'r') as handle:
			lines = handle.readlines()
			for line in lines:
				line = line.decode('utf-8')
				if not line: continue
				name, d, value = [ token.strip() for token in line.partition(':')]
				if name in self.allowed_sections and hasattr(self, name.encode('utf-8')):
					getattr(self, name)(post, value)
				else:
					#found post text line
					post['text'].append(line)
					
		if not 'title' in post.keys():
			print 'Oups, post %s has no title!' % filename
			sys.exit(-1)
		if not 'tags' in post.keys():
			print 'Oups, post %s has no tags!' % filename
			sys.exit(-1)
		if not 'text' in post.keys():
			print 'Oups, post %s has no text!' % filename
			sys.exit(-1)
		if not 'date' in post.keys():
			print 'Oups, post %s has no date!' % filename
			sys.exit(-1)

		post['id'] = self.PostID(post)
		return post
		
	def PostID(self, post):
		postId = post['title']
		for ch in [' ', ',', '.', '!', '?', ';', ':', '/', '-']:
			if ch in postId:
				postId = postId.replace(ch, '-')		
		return helpers.tr(postId)
		
	def GenerateResources(self):
		if self.options.skip_resources:
			return
			
		outputResourcesFolder = os.path.join(self.options.target, defines.resources)
		if not os.path.exists(outputResourcesFolder):
			os.makedirs(outputResourcesFolder)
		
		print 'Generating resources'
		os.system('cp -r %s/* %s' % (os.path.join(self.options.source, defines.inResources), outputResourcesFolder) )
		
	def GeneratePost(self, post):
		if self.options.skip_posts:
			return
		outputPostsFolder = os.path.join(self.options.target, defines.posts)
		postPath = os.path.join(os.path.join(outputPostsFolder, 'id', helpers.tr(post['id'])))
		if not os.path.exists(postPath):
			logging.debug('creaing %s' % postPath)
			os.makedirs(postPath)
		postByDatePath = os.path.join(outputPostsFolder, 'date', 
			str(post['date'].year), str(post['date'].month), 
			str(post['date'].day), helpers.tr(post['id']))
		if not os.path.exists(postByDatePath):
			logging.debug('creating %s' % postByDatePath)
			os.makedirs(postByDatePath)
		
		logging.debug('Generating post: %s' % os.path.join(postPath, 'index.html'))
		with open( os.path.join(postPath, 'index.html'), 'w') as postFile:
			template = self.templates.get_template(defines.postTemplate)
			postFile.write( template.render( encoding = 'utf-8', helpers = helpers, post = post) )
		
		os.system('cp %s %s' % (os.path.abspath(os.path.join(postPath, 'index.html')), os.path.abspath(postByDatePath)) )
		
	def GeneratePage(self, pageNumber, totalPages, page):
		if self.options.skip_pages:
			return
			
		outputPagesFolder = os.path.join(self.options.target, defines.pages)
		if not os.path.exists(os.path.join(outputPagesFolder, str(pageNumber))):
			os.makedirs(os.path.join(outputPagesFolder, str(pageNumber)))
			
		pagePath = os.path.join(outputPagesFolder, str(pageNumber), 'index.html')
		logging.debug('Generating page #%d with %d posts: %s' % (pageNumber, len(page), pagePath) )
		self._GeneratePage(pagePath, pageNumber, totalPages, page, filters = {})
		
	def GeneragteTagPage(self, pageNumber, totalPages, page, tag):
		if self.options.skip_tags:
			return
		outputTagsFolder = os.path.join(self.options.target, defines.tags)
		if not os.path.exists(os.path.join(outputTagsFolder, helpers.tr(tag), str(pageNumber))):
			os.makedirs(os.path.join(outputTagsFolder, helpers.tr(tag), str(pageNumber)))
		
		pagePath = os.path.join(outputTagsFolder, helpers.tr(tag), str(pageNumber), 'index.html')
		logging.debug('Generating tag %s page #%d with %d posts: %s' % ( 
				helpers.tr(tag), pageNumber, 
				len(page), pagePath) )
		self._GeneratePage(pagePath, pageNumber, totalPages, page, filters = {'tag' : tag})
			
	def _GeneratePage(self, pagePath, pageNumber, totalPages, page, filters = {}):
		with open(pagePath, 'w') as pageFile:
			template = self.templates.get_template(defines.pageTemplate)
			pageFile.write( template.render( encoding = 'utf-8', 
					helpers = helpers,	
					filters = filters,
					pageNumber = pageNumber,
					totalPages = totalPages, 
					page = page) )
		
	def GenerateIndexes(self, tags, posts, pages, dates, monthsByPosts):
		if self.options.skip_indexes:
			return
			
		print 'Generating indexes'
		outputPagesFolder = os.path.join(self.options.target, defines.pages)
		outputPostsFolder = os.path.join(self.options.target, defines.posts)
		outputTagsFolder = os.path.join(self.options.target, defines.tags)
		#create '/post/' -> '/pages/1' handler
		src = os.path.join(outputPagesFolder, '1/index.html')
		dst = os.path.join(outputPostsFolder, 'index.html')
		logging.debug('Link %s -> %s' % (src, dst))
		os.system('cp %s %s' % (os.path.abspath(src), os.path.abspath(dst)) )
		
		#create '/tag/%name' -> '/tag/%name/1' handler
		for tag in tags:
			logging.debug('Generating index for tag %s' % helpers.tr(tag))
			src = os.path.join(outputTagsFolder, '%s/1/index.html' % helpers.tr(tag))
			dst = os.path.join(outputTagsFolder, '%s/index.html' % helpers.tr(tag))
			logging.debug('Link %s -> %s' % (src, dst))
			os.system('cp %s %s' % (os.path.abspath(src), os.path.abspath(dst)) )
			
		#create /index.html with overview
		logging.debug('Generating index.html')
		indexPath = os.path.join(self.options.target, 'index.html')
		with open(indexPath, 'w') as indexFile:
			template = self.templates.get_template(defines.indexTemplate)
			indexFile.write( template.render( encoding = 'utf-8', 
					helpers = helpers, 
					tags = tags, 
					posts = posts,
					pages = pages,
					dates = dates,
					years = self.options.years,
					monthsByPosts = monthsByPosts) )
					
	def _GenerateFeed(self, feedPath, webRoot, postSizes, posts, title, desc):
			logging.debug('Generating feed with %d items: %s' % (len(posts), feedPath) )
			feedTemplate = Template(rssTemplate)
			with open(feedPath, 'w') as feedFile:
				#Render reed template to file
				feedFile.write(feedTemplate.render_unicode(
					title = title,
					url = self.options.url,
					desc = desc,
					lang = self.options.lang,
					posts = posts,
					helpers = helpers,
					cut_at = self.options.cut_at,
					webRoot = webRoot,
					os = os,
					postSizes = postSizes).encode('utf-8', 'replace'))
	
	def GenerateFeeds(self, posts, tags):
		if self.options.skip_rss:
			return
			
		print 'Generating feeds'
		
		outputPostsFolder = os.path.join(self.options.target, defines.posts, 'id')
		outputTagsFolder = os.path.join(self.options.target, defines.tags)
		
		postSizes = {}
		#Get post sizes
		for postFolder in os.listdir(os.path.join(outputPostsFolder)):
			if os.path.isdir(os.path.join(outputPostsFolder, postFolder)):
				postSizes[postFolder] = os.path.getsize(os.path.join(outputPostsFolder, postFolder, 'index.html'))
		
		#Posts feed
		postsFeedPath = os.path.join(self.options.target, defines.posts, 'feed.rss')
		postsTitle = 'Posts of %s' % self.options.title
		postsDesc = 'Last %d posts of %s' % (self.options.items, self.options.title)
		self._GenerateFeed(postsFeedPath, self.options.webroot + '/post/id', postSizes, posts[:self.options.items], postsTitle, postsDesc)
		
		#Tag feeds
		for tag in tags.keys():
			tagFeedPath = os.path.join(outputTagsFolder, helpers.tr(tag), 'feed.rss')
			postsWithTag = tags[tag]
			tagTitle = 'Posts of %s with tag %s' % (self.options.title, tag)
			tagDesc = 'Last %d posts of %s with tag %s' % ( len(postsWithTag), self.options.title, tag)
			self._GenerateFeed(tagFeedPath, self.options.webroot + '/tag/%s' % helpers.tr(tag), postSizes, postsWithTag, tagTitle, tagDesc)
		print '  totally %d tag feeds written' % len(tags.keys())
			
	def GenerateSiteMap(self, posts, tags, pages, dates):
		if self.options.skip_sitemap:
			return
			
		print 'Generating Site map'
		siteMapPath = os.path.join(self.options.target, 'blog.sitemap')
		logging.debug('Generating site map with %d post, %d tag pages & %d pages: %s' % ( len(posts), len(tags), len(pages), siteMapPath))
		tmpl = Template(siteMapTemplate)
		with open(siteMapPath, 'w') as sitemapFile:
			#Render feed template to file
			sitemapFile.write(tmpl.render_unicode(
				helpers = helpers,
				posts = posts,
				tags = tags,
				pages = pages,
				dates = dates,
				years = self.options.years,
				url = self.options.url,
				webRoot = self.options.webroot
			).encode('utf-8', 'replace'))
		
		
	def Generate(self):
		logging.debug('Reading site %s' % self.options.source)
		postsFolder = os.path.join(self.options.source, defines.inPosts)
		
		posts = []
		pages = {}
		tags = {}
		dates = {}
		for y in self.options.years:
			dates[y] = {}
			for m in range(1, 12): 
				dates[y][m] = {}
				for d in range(1, 32):
					dates[y][m][d] = []
		
		#Parse *.md files and populate posts list
		print 'Generating post pages'
		for postFile in [p for p in os.listdir(postsFolder) if p.endswith('.md')]:
			post = self.ParsePost(os.path.join(postsFolder, postFile))
			posts.append(post)
			#append to tags
			for tag in post['tags']:
				if not tag in tags:
					tags[tag] = []
				tags[tag].append(post)
			#append to date dicts
			dates[post['date'].year][post['date'].month][post['date'].day].append(post)
			self.GeneratePost(post)
		print '  totaly %d posts written' % len(posts)
		#Sort posts by date
		posts.sort()
		posts.reverse()
		
		#Process posts
		print 'Building post pages'
		postIndex = 0
		pageNumber = 0;
		logging.debug('Posts per page: %d' % self.options.posts)
		for post in posts:
			if postIndex == 0 or postIndex + 1 > self.options.posts:
				pageNumber += 1
				postIndex = 0
				logging.debug('Page started: %d' % pageNumber)
				pages[pageNumber] = []
			pages[pageNumber].append(post)
			postIndex += 1
			
		for pageNumber in pages:
			self.GeneratePage(pageNumber, len(pages), pages[pageNumber])
		print '  totally %d pages written' % len(pages)
		#Process posts & build pages for tags		
		for tag in tags:
			postsWithTag = tags[tag]
			
			#Sort posts with tag by date
			postsWithTag.sort()
			postsWithTag.reverse()
			
			logging.debug('Processing tag %s with %d posts' % ( tag, len(postsWithTag) ))
			totalPagesWithTag = len(postsWithTag) / self.options.posts
			postPage = []
			tagPageNumber = 1
			postIndex = 0
			for post in postsWithTag:
				postPage.append(post)
				if postIndex == self.options.posts or (postIndex + 1 == len(postsWithTag)):
					self.GeneragteTagPage(tagPageNumber, totalPagesWithTag, postPage, tag)
					postPage = []
					tagPageNumber += 1
					
				postIndex += 1
			
		#Generate dates
		print 'Generating dates'
		outputPostsFolder = os.path.join(self.options.target, defines.posts)
		totalDatePages = 0
		monthsByPosts = []
		for y in self.options.years:
			if not y in dates:
				continue
			for m in range(1, 12):
				postsByMonth = []
				#Generate pages for days
				for d in range(1, 31):
					postByDay = dates[y][m][d]
					if postByDay:
						#append to month posts
						[postsByMonth.append(p) for p in postByDay]
						postsByDayPath = os.path.join(outputPostsFolder, 'date', str(y), str(m), str(d), 'index.html')
						self._GeneratePage(postsByDayPath, 1, 1, postByDay, filters = {'year' : y, 'month': m, 'day': d})
						totalDatePages += 1
						
				#Generate page for month
				if postsByMonth:
					monthsByPosts.append(m)
					postsByMonthPath = os.path.join(outputPostsFolder, 'date', str(y), str(m), 'index.html')
					self._GeneratePage(postsByMonthPath, 1, 1, postsByMonth, filters = {'year' : y, 'month': m})				
					totalDatePages +=1
		print '  totally %d date pages written' % totalDatePages
		
		self.GenerateResources()
		self.GenerateIndexes([tag for tag in tags], posts, pages, dates, monthsByPosts)
		self.GenerateFeeds(posts, tags)
		self.GenerateSiteMap(posts, tags, pages, dates)
		
		print 'Done.'