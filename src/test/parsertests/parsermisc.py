#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import unittest
import hashlib

from test.utils import removeWiki

from outwiker.core.tree import WikiDocument
from outwiker.core.attachment import Attachment
from outwiker.core.application import Application

from pages.wiki.parser.wikiparser import Parser
from pages.wiki.wikipage import WikiPageFactory
from pages.wiki.parserfactory import ParserFactory


class ParserMiscTest (unittest.TestCase):
	def setUp(self):
		self.encoding = "utf8"

		self.filesPath = u"../test/samplefiles/"

		self.__createWiki()
		
		factory = ParserFactory()
		self.parser = factory.make (self.testPage, Application.config)
	

	def __createWiki (self):
		# Здесь будет создаваться вики
		self.path = u"../test/testwiki"
		removeWiki (self.path)

		self.rootwiki = WikiDocument.create (self.path)
		WikiPageFactory.create (self.rootwiki, u"Страница 2", [])
		self.testPage = self.rootwiki[u"Страница 2"]
		

	def tearDown(self):
		removeWiki (self.path)


	def testHorLine (self):
		text = u"бла-бла-бла \nкхм ---- бла-бла-бла\nбла-бла-бла"
		result = u'бла-бла-бла \nкхм <HR> бла-бла-бла\nбла-бла-бла'

		self.assertEqual (self.parser.toHtml (text), result, self.parser.toHtml (text).encode (self.encoding))


	def testParseWithoutAttaches (self):
		pagetitle = u"Страница 666"
		
		WikiPageFactory.create (self.rootwiki, pagetitle, [])
		parser = Parser(self.rootwiki[pagetitle], Application.config)

		parser.toHtml (u"Attach:bla-bla-bla")
