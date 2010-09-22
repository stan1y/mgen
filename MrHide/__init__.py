#
# Mr. Hide Site Genetator
# Copyright Stanislav Yudin, 2010
#

__version__ = '0.2'

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

rssTemplate = '''
# -*- encoding:utf-8 -*-

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
				<description>${helpers.markdown.markdown(helpers.cut(''.join(post['text']), cut_at))}</description>
				<enclosure
					url="${url + webRoot + '/' + post['id']}"
					type="text/html"
					length="${postSize}" />
			</item>
		%endfor
   </channel>
</rss>
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
		post['date'] = datetime.datetime.strptime(value.strip(), '%d.%m.%Y')
	def tags(self, post, value):
		try:
			if self.options.transliterate:
				from unidecode import unidecode
				post['tags'] = [ helpers.urllib.quote(unidecode(tag.strip())) for tag in value.split(',') if tag]
			else:
				post['tags'] = [ helpers.urllib.quote(tag.strip()) for tag in value.split(',') if tag]
		except ImportError:
			print 'Transliteration is OFF, unidecode not found' 
			post['tags'] = [ helpers.urllib.quote(tag.strip()) for tag in value.split(',') if tag]
		
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
		
		post['id'] = self.PostID(post)
		return post
		
	def PostID(self, post):
		postId = post['title']
		for ch in [' ', ',', '.', '!', '?', ';', ':', '/', '-']:
			if ch in postId:
				postId = postId.replace(ch, '-')		
		try:
			if self.options.transliterate:
				from unidecode import unidecode
				return unidecode(postId)
			else:
				return postId
		except ImportError:
			print 'Transliteration is OFF, unidecode not found'
			return postId
		
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
		if not os.path.exists(os.path.join(outputPostsFolder, post['id'].encode('utf-8'))):
			os.makedirs(os.path.join(outputPostsFolder, post['id'].encode('utf-8')))
		
		postPath = os.path.join(outputPostsFolder, post['id'].encode('utf-8'), 'index.html')
		logging.debug('Generating post: %s' % postPath)
		with open(postPath, 'w') as postFile:
			template = self.templates.get_template(defines.postTemplate)
			postFile.write( template.render( encoding = 'utf-8', helpers = helpers, post = post) )
		
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
		if not os.path.exists(os.path.join(outputTagsFolder, tag.encode('utf-8'), str(pageNumber))):
			os.makedirs(os.path.join(outputTagsFolder, tag.encode('utf-8'), str(pageNumber)))
		
		pagePath = os.path.join(outputTagsFolder, tag.encode('utf-8'), str(pageNumber), 'index.html')
		logging.debug('Generating tag %s page #%d with %d posts: %s' % (tag.encode('utf-8'), pageNumber, len(page), pagePath) )
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
		
	def GenerateIndexes(self, tags, posts, pages):
		if self.options.skip_indexes:
			return
			
		print 'Generating indexes'
		outputPagesFolder = os.path.join(self.options.target, defines.pages)
		outputPostsFolder = os.path.join(self.options.target, defines.posts)
		outputTagsFolder = os.path.join(self.options.target, defines.tags)
		#create '/post/' -> '/pages/1' handler
		src = os.path.join(outputPagesFolder, '1/index.html')
		dst = os.path.join(outputPostsFolder, 'index.html')
		logging.debug('Copy %s %s' % (src, dst))
		os.system('cp %s %s' % (src, dst) )
		
		#create '/tag/%name' -> '/tag/%name/1' handler
		for tag in tags:
			src = os.path.join(outputTagsFolder, '%s/1/index.html' % tag.encode('utf-8'))
			dst = os.path.join(outputTagsFolder, '%s/index.html' % tag.encode('utf-8'))
			logging.debug('Copy %s %s' % (src, dst))
			os.system('cp %s %s' % (src, dst) )
			
		#create /index.html with overview
		logging.debug('Generating index.html')
		indexPath = os.path.join(self.options.target, 'index.html')
		with open(indexPath, 'w') as indexFile:
			template = self.templates.get_template(defines.indexTemplate)
			indexFile.write( template.render( encoding = 'utf-8', 
					helpers = helpers, 
					tags = tags, 
					posts = posts,
					pages = pages) )
					
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
			
		print 'Generating Feeds'
		
		outputPostsFolder = os.path.join(self.options.target, defines.posts)
		outputTagsFolder = os.path.join(self.options.target, defines.tags)
		
		postSizes = {}
		#Get post sizes
		for postFolder in os.listdir(outputPostsFolder):
			if os.path.isdir(os.path.join(outputPostsFolder, postFolder)):
				postSizes[postFolder] = os.path.getsize(os.path.join(outputPostsFolder, postFolder, 'index.html'))
		
		#Posts feed
		postsFeedPath = os.path.join(outputPostsFolder, 'feed.rss')
		postsTitle = 'Posts of %s' % self.options.title
		postsDesc = 'Last %d posts of %s' % (self.options.items, self.options.title)
		self._GenerateFeed(postsFeedPath, '/post/', postSizes, posts[:self.options.items], postsTitle, postsDesc)
		
		#Tag feeds
		for tag in tags.keys():
			tagFeedPath = os.path.join(outputTagsFolder, tag, 'feed.rss')
			postsWithTag = tags[tag]
			tagTitle = 'Posts of %s with tag %s' % (self.options.title, tag)
			tagDesc = 'Last %d posts of %s with tag %s' % ( len(postsWithTag), self.options.title, tag)
			self._GenerateFeed(tagFeedPath, '/tag/%s' % tag, postSizes, postsWithTag, tagTitle, tagDesc)
		
	def Generate(self):
		logging.debug('Reading site %s' % self.options.source)
		postsFolder = os.path.join(self.options.source, defines.inPosts)
		
		posts = []
		pages = {}
		tags = {}
		
		#Parse *.md files and populate posts list
		print 'Processing posts'
		for postFile in [p for p in os.listdir(postsFolder) if p.endswith('.md')]:
			post = self.ParsePost(os.path.join(postsFolder, postFile))
			posts.append(post)
			for tag in post['tags']:
				if not tag in tags:
					tags[tag] = []
				tags[tag].append(post)
				
			self.GeneratePost(post)
		
		#Sort posts by date
		posts.sort()
		posts.reverse()
		
		#Paginate posts
		print 'Pagingting posts'
		postIndex = 0
		pageNumber = 0;
		logging.debug('Post per page: %d' % self.options.posts)
		for post in posts:
			if postIndex == 0 or postIndex + 1 > self.options.posts:
				pageNumber += 1
				postIndex = 0
				logging.debug('Page started: %d' % pageNumber)
				pages[pageNumber] = []
			pages[pageNumber].append(post)
			postIndex += 1
		
		print 'Generating %d pages' % len(pages)
		for pageNumber in pages:
			self.GeneratePage(pageNumber, len(pages), pages[pageNumber])
		
		#Paginate posts with tags
		print 'Generating %d tag pages' % len(tags)
		for tag in tags:
			print 'Processing tag %s' % tag.encode('utf-8')
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
		
		self.GenerateFeeds(posts, tags)
		self.GenerateResources()
		self.GenerateIndexes([tag for tag in tags], posts, pages)
		
		print 'Done.'