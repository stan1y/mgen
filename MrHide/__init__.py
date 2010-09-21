
__version__ = '0.1'

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

class MrHide(object):
	def __init__(self, options):
		if options.debug:
			logging.basicConfig(level = logging.DEBUG)

		self.options = options	
		
		helpers.webroot = options.webroot
		
		print 'Mr.Hide ver. %s' % __version__
		print 'Source		: %s' % options.source
		print 'Output		: %s' % options.target
		print 'Webroot		: %s' % options.webroot
		print 'Geneator Options'
		print 'Posts		: %s' % yesno( not options.skip_posts )
		print 'Pages		: %s' % yesno( not options.skip_pages)
		print 'Tags		: %s' % yesno( not options.skip_tags)
		print 'Resources	: %s' % yesno( not options.skip_tags)
		
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
		
		post['id'] = self.PostID(post)
		return post
		
	def PostID(self, post):
		return post['title'].replace(' ', '-')
		
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
		if not os.path.exists(os.path.join(outputPostsFolder, post['id'])):
			os.makedirs(os.path.join(outputPostsFolder, post['id']))
		
		postPath = os.path.join(outputPostsFolder, post['id'], 'index.html')
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
		if not os.path.exists(os.path.join(outputTagsFolder, tag, str(pageNumber))):
			os.makedirs(os.path.join(outputTagsFolder, tag, str(pageNumber)))
		
		pagePath = os.path.join(outputTagsFolder, tag, str(pageNumber), 'index.html')
		logging.debug('Generating tag %s page #%d with %d posts: %s' % (tag, pageNumber, len(page), pagePath) )
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
		print 'Generating %d tags' % len(tags)
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
				if postIndex == self.options.posts or len(postsWithTag) < self.options.posts:
					self.GeneragteTagPage(tagPageNumber, totalPagesWithTag, postPage, tag)
					postPage = []
					tagPageNumber += 1
					
				postIndex += 1
		
		self.GenerateResources()
		self.GenerateIndexes([tag for tag in tags], posts, pages)
		
		print 'Done.'