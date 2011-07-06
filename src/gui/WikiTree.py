# -*- coding: utf-8 -*-
# generated by wxGlade 0.6.3 on Mon Apr 05 21:59:12 2010

import os
import os.path
import ConfigParser

import wx

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode

# end wxGlade

from core.application import Application
import core.exceptions
import core.commands
import core.system
import gui.pagedialog
from core.config import BooleanOption


class WikiTree(wx.Panel):
	def __init__(self, *args, **kwds):
		self.ID_ADD_CHILD = wx.NewId()
		self.ID_ADD_SIBLING = wx.NewId()
		self.ID_RENAME = wx.NewId()
		self.ID_REMOVE = wx.NewId()
		self.ID_PROPERTIES_BUTTON = wx.NewId()
		self.ID_PROPERTIES_POPUP = wx.NewId()
		self.ID_MOVE_UP = wx.NewId()
		self.ID_MOVE_DOWN = wx.NewId()
		self.ID_ADD_SIBLING_PAGE = wx.NewId()
		self.ID_ADD_CHILD_PAGE = wx.NewId()
		self.ID_REMOVE_PAGE = wx.NewId()
		
		self.ID_COPY_PATH = wx.NewId()
		self.ID_COPY_ATTACH_PATH = wx.NewId()
		self.ID_COPY_TITLE = wx.NewId()
		self.ID_COPY_LINK = wx.NewId()

		# begin wxGlade: WikiTree.__init__
		kwds["style"] = wx.TAB_TRAVERSAL
		wx.Panel.__init__(self, *args, **kwds)
		self.toolbar = self.getToolbar(self, -1)
		self.treeCtrl = wx.TreeCtrl(self, -1, style=wx.TR_HAS_BUTTONS|wx.TR_NO_LINES|wx.TR_LINES_AT_ROOT|wx.TR_EDIT_LABELS|wx.TR_DEFAULT_STYLE|wx.SUNKEN_BORDER)

		self.__set_properties()
		self.__do_layout()
		# end wxGlade

		self.defaultIcon = os.path.join (core.system.getImagesDir(), "page.png")
		self.iconHeight = 16

		self.defaultBitmap = wx.Bitmap (self.defaultIcon)
		assert self.defaultBitmap.IsOk()
		
		self.defaultBitmap.SetHeight (self.iconHeight)

		self.dragItem = None
	
		# Картинки для дерева
		self.imagelist = wx.ImageList(16, self.iconHeight)
		self.treeCtrl.AssignImageList (self.imagelist)

		# Кеш для страниц, чтобы было проще искать элемент дерева по странице
		# Словарь. Ключ - страница, значение - элемент дерева wx.TreeItemId
		self._pageCache = {}

		self.__createPopupMenu()

		# Элемент, над которым показываем меню
		self.popupItem = None

		# Секция настроек куда сохраняем развернутость страницы
		self.pageOptionsSection = u"Tree"

		# Имя опции для сохранения развернутости страницы
		self.pageOptionExpand = "Expand"

		self.BindGuiEvents()
		self.BindApplicationEvents()
		self.BindPopupMenuEvents()


	def BindApplicationEvents(self):
		"""
		Подписка на события контроллера
		"""
		Application.onTreeUpdate += self.onTreeUpdate
		Application.onPageCreate += self.onPageCreate
		Application.onPageOrderChange += self.onPageOrderChange
		Application.onPageSelect += self.onPageSelect
		Application.onPageRemove += self.onPageRemove

		Application.onStartTreeUpdate += self.onStartTreeUpdate
		Application.onEndTreeUpdate += self.onEndTreeUpdate
		
		# События, связанные с рендерингом страниц
		Application.onHtmlRenderingBegin += self.onHtmlRenderingBegin
		Application.onHtmlRenderingEnd += self.onHtmlRenderingEnd


	def UnBindApplicationEvents(self):
		"""
		Отписка от событий контроллера
		"""
		Application.onTreeUpdate -= self.onTreeUpdate
		Application.onPageCreate -= self.onPageCreate
		Application.onPageOrderChange -= self.onPageOrderChange
		Application.onPageSelect -= self.onPageSelect
		Application.onPageRemove -= self.onPageRemove

		Application.onStartTreeUpdate -= self.onStartTreeUpdate
		Application.onEndTreeUpdate -= self.onEndTreeUpdate
		
		# События, связанные с рендерингом страниц
		Application.onHtmlRenderingBegin -= self.onHtmlRenderingBegin
		Application.onHtmlRenderingEnd -= self.onHtmlRenderingEnd
	

	def BindGuiEvents (self):
		"""
		Подписка на события интерфейса
		"""
		# События, связанные с деревом
		self.Bind (wx.EVT_TREE_SEL_CHANGED, self.onSelChanged)

		# Перетаскивание элементов
		self.treeCtrl.Bind (wx.EVT_TREE_BEGIN_DRAG, self.onBeginDrag)
		self.treeCtrl.Bind (wx.EVT_TREE_END_DRAG, self.onEndDrag)
		
		# Переименование элемента
		self.treeCtrl.Bind (wx.EVT_TREE_END_LABEL_EDIT, self.onEndLabelEdit)

		# Показ всплывающего меню
		self.treeCtrl.Bind (wx.EVT_TREE_ITEM_MENU, self.onItemMenu)
		
		# Сворачивание/разворачивание элементов
		self.treeCtrl.Bind (wx.EVT_TREE_ITEM_COLLAPSED, self.onTreeStateChanged)
		self.treeCtrl.Bind (wx.EVT_TREE_ITEM_EXPANDED, self.onTreeStateChanged)

		self.treeCtrl.Bind (wx.EVT_TREE_ITEM_ACTIVATED, self.onTreeItemActivated)

		self.Bind(wx.EVT_MENU, self.onMoveUp, id=self.ID_MOVE_UP)
		self.Bind(wx.EVT_MENU, self.onMoveDown, id=self.ID_MOVE_DOWN)
		self.Bind(wx.EVT_MENU, self.onAddSiblingPage, id=self.ID_ADD_SIBLING_PAGE)
		self.Bind(wx.EVT_MENU, self.onAddChildPage, id=self.ID_ADD_CHILD_PAGE)
		self.Bind(wx.EVT_MENU, self.onRemovePage, id=self.ID_REMOVE_PAGE)
		
		self.Bind(wx.EVT_MENU, self.onPropertiesButton, id=self.ID_PROPERTIES_BUTTON)

		self.Bind (wx.EVT_CLOSE, self.onClose)


	def onClose (self, event):
		self.UnBindApplicationEvents()


	def onPropertiesButton (self, event):
		if Application.selectedPage != None:
			gui.pagedialog.editPage (self, Application.selectedPage)


	def onPageCreate (self, newpage):
		"""
		Обработка создания страницы
		"""
		parentItem = self._pageCache[newpage.parent]
		self.insertChild (newpage, parentItem)


	def onAddSiblingPage (self, event):
		gui.pagedialog.createSiblingPage (self)


	def onAddChildPage (self, event):
		gui.pagedialog.createChildPage (self)


	def onRemovePage (self, event):
		if Application.wikiroot != None and Application.wikiroot.selectedPage != None:
			core.commands.removePage (Application.wikiroot.selectedPage)


	def onMoveUp (self, event):
		core.commands.moveCurrentPageUp()


	def onMoveDown (self, event):
		core.commands.moveCurrentPageDown()


	def onPageRemove (self, page):
		self._removePageItem (page)
	

	def onTreeItemActivated (self, event):
		"""
		"""
		item = event.GetItem()
		if not item.IsOk():
			return

		page = self.treeCtrl.GetItemData (item).GetData()
		gui.pagedialog.editPage (self, page)
		

	def BindPopupMenuEvents (self):
		"""
		События, связанные с контекстным меню
		"""
		self.Bind(wx.EVT_MENU, self.onAddChild, id=self.ID_ADD_CHILD)
		self.Bind(wx.EVT_MENU, self.onAddSibling, id=self.ID_ADD_SIBLING)
		self.Bind(wx.EVT_MENU, self.onRename, id=self.ID_RENAME)
		self.Bind(wx.EVT_MENU, self.onRemove, id=self.ID_REMOVE)
		
		self.Bind(wx.EVT_MENU, self.onCopyTitle, id=self.ID_COPY_TITLE)
		self.Bind(wx.EVT_MENU, self.onCopyPath, id=self.ID_COPY_PATH)
		self.Bind(wx.EVT_MENU, self.onCopyAttachPath, id=self.ID_COPY_ATTACH_PATH)
		self.Bind(wx.EVT_MENU, self.onCopyLink, id=self.ID_COPY_LINK)

		self.Bind(wx.EVT_MENU, self.onPropertiesPopup, id=self.ID_PROPERTIES_POPUP)
	

	def onHtmlRenderingBegin (self, page, htmlView):
		self.treeCtrl.Disable()
		self.treeCtrl.Update()

	
	def onHtmlRenderingEnd (self, page, htmlView):
		self.treeCtrl.Enable()


	def onTreeStateChanged (self, event):
		item = event.GetItem()
		assert item.IsOk()
		self.__saveItemState (item)


	def __saveItemState (self, itemid):
		assert itemid.IsOk()

		page = self.treeCtrl.GetItemData (itemid).GetData()
		expanded = self.treeCtrl.IsExpanded (itemid)
		expandedOption = BooleanOption (page.params, self.pageOptionsSection, self.pageOptionExpand, False)

		try:
			expandedOption.value = expanded
		except IOError as e:
			core.commands.MessageBox (_(u"Can't save page options\n%s") % (unicode (e)),
					_(u"Error"), wx.ICON_ERROR | wx.OK)


	def _loadExpandState (self, page):
		if page.parent != None:
			try:
				expanded = page.params.getbool (self.pageOptionsSection, self.pageOptionExpand)
			except ConfigParser.NoSectionError:
				return
			except ConfigParser.NoOptionError:
				return

			if expanded:
				self.treeCtrl.Expand (self._pageCache[page])


	def onRemove (self, event):
		"""
		Удалить страницу
		"""
		assert self.popupItem != None
		assert self.popupItem.IsOk()

		page = self.treeCtrl.GetItemData (self.popupItem).GetData()
		assert page != None

		core.commands.removePage (page)


	def onCopyLink (self, event):
		"""
		Копировать ссылку на страницу в буфер обмена
		"""
		assert self.popupItem != None
		assert self.popupItem.IsOk()

		page = self.treeCtrl.GetItemData (self.popupItem).GetData()
		assert page != None

		core.commands.copyLinkToClipboard (page)

	
	def onCopyTitle (self, event):
		"""
		Копировать заголовок страницы в буфер обмена
		"""
		assert self.popupItem != None
		assert self.popupItem.IsOk()

		page = self.treeCtrl.GetItemData (self.popupItem).GetData()
		assert page != None

		core.commands.copyTitleToClipboard (page)

	
	def onCopyPath (self, event):
		"""
		Копировать путь до страницы в буфер обмена
		"""
		assert self.popupItem != None
		assert self.popupItem.IsOk()

		page = self.treeCtrl.GetItemData (self.popupItem).GetData()
		assert page != None

		core.commands.copyPathToClipboard (page)


	def onCopyAttachPath (self, event):
		"""
		Копировать путь до прикрепленных файлов в буфер обмена
		"""
		assert self.popupItem != None
		assert self.popupItem.IsOk()

		page = self.treeCtrl.GetItemData (self.popupItem).GetData()
		assert page != None

		core.commands.copyAttachPathToClipboard (page)


	def __createPopupMenu (self):
		self.popupMenu = wx.Menu ()
		self.popupMenu.Append (self.ID_ADD_CHILD, _(u"Add Child Page…"))
		self.popupMenu.Append (self.ID_ADD_SIBLING, _(u"Add Sibling Page…"))
		self.popupMenu.Append (self.ID_RENAME, _(u"Rename"))
		self.popupMenu.Append (self.ID_REMOVE, _(u"Remove…"))
		self.popupMenu.AppendSeparator()
		
		self.popupMenu.Append (self.ID_COPY_TITLE, _(u"Copy Page Title"))
		self.popupMenu.Append (self.ID_COPY_PATH, _(u"Copy Page Path"))
		self.popupMenu.Append (self.ID_COPY_ATTACH_PATH, _(u"Copy Attaches Path"))
		self.popupMenu.Append (self.ID_COPY_LINK, _(u"Copy Page Link"))
		self.popupMenu.AppendSeparator()

		self.popupMenu.Append (self.ID_PROPERTIES_POPUP, _(u"Properties…"))
	

	def onRename (self, event):
		assert self.popupItem != None
		assert self.popupItem.IsOk()

		self.treeCtrl.EditLabel (self.popupItem)
	

	def onAddChild (self, event):
		assert self.popupItem != None
		assert self.popupItem.IsOk()

		page = self.treeCtrl.GetItemData (self.popupItem).GetData()
		assert page != None

		gui.pagedialog.createPageWithDialog (self, page)

	
	def onAddSibling (self, event):
		assert self.popupItem != None
		assert self.popupItem.IsOk()

		page = self.treeCtrl.GetItemData (self.popupItem).GetData()
		assert page != None
		assert page.parent != None

		gui.pagedialog.createPageWithDialog (self, page.parent)

	
	def onPropertiesPopup (self, event):
		assert self.popupItem != None
		assert self.popupItem.IsOk()

		page = self.treeCtrl.GetItemData (self.popupItem).GetData()
		assert page != None

		if page.parent != None:
			gui.pagedialog.editPage (self, page)
	

	def onItemMenu (self, event):
		self.popupItem = event.GetItem()
		if not self.popupItem.IsOk ():
			return

		self.PopupMenu (self.popupMenu)
	

	def beginRename (self):
		selectedItem = self.treeCtrl.GetSelection()
		if not selectedItem.IsOk():
			return

		self.treeCtrl.EditLabel (selectedItem)


	def onEndLabelEdit (self, event):
		if event.IsEditCancelled():
			return

		# Новый заголовок
		label = event.GetLabel().strip()

		item = event.GetItem()
		page = self.treeCtrl.GetItemData (item).GetData()
		
		# Не доверяем переименовывать элементы системе
		event.Veto()

		core.commands.renamePage (page, label)


	def onStartTreeUpdate (self, root):
		self._unbindUpdateEvents()
	

	def _unbindUpdateEvents (self):
		Application.onTreeUpdate -= self.onTreeUpdate
		Application.onPageCreate -= self.onPageCreate
		Application.onPageSelect -= self.onPageSelect
		Application.onPageOrderChange -= self.onPageOrderChange
		self.Unbind (wx.EVT_TREE_SEL_CHANGED, handler = self.onSelChanged)

	
	def onEndTreeUpdate (self, root):
		self._bindUpdateEvents()
		self.treeUpdate (Application.wikiroot)


	def _bindUpdateEvents (self):
		Application.onTreeUpdate += self.onTreeUpdate
		Application.onPageCreate += self.onPageCreate
		Application.onPageSelect += self.onPageSelect
		Application.onPageOrderChange += self.onPageOrderChange
		self.Bind (wx.EVT_TREE_SEL_CHANGED, self.onSelChanged)

	
	def onBeginDrag (self, event):
		event.Allow()
		self.dragItem = event.GetItem()
		self.treeCtrl.SetFocus()


	def onEndDrag (self, event):
		if self.dragItem != None:
			# Элемент, на который перетащили другой элемент (self.dragItem)
			endDragItem = event.GetItem()

			# Перетаскиваемая станица
			draggedPage = self.treeCtrl.GetItemData (self.dragItem).GetData()

			# Будущий родитель для страницы
			if endDragItem.IsOk():
				newParent = self.treeCtrl.GetItemData (endDragItem).GetData()
				core.commands.movePage (draggedPage, newParent)

		self.dragItem = None


	def onTreeUpdate (self, sender):
		self.treeUpdate (sender.root)


	def onPageSelect (self, page):
		"""
		Изменение выбранной страницы
		"""
		currpage = self.selectedPage
		if currpage != page:
			self.selectedPage = page


	def onSelChanged (self, event):
		page = self.selectedPage
		if page.root.selectedPage != page:
			page.root.selectedPage = page
	

	def onPageOrderChange (self, sender):
		"""
		Изменение порядка страниц
		"""
		self._updatePage (sender)
	

	def moveBranch (self, page):
		"""
		Переместить узел, связанный со страницей в новое положение без обновления всего дерева
		"""
		item = self._pageCache[page]
		parentItem = self._pageCache[page.parent]
	

	@property
	def selectedPage (self):
		item = self.treeCtrl.GetSelection ()
		if item.IsOk():
			page = self.treeCtrl.GetItemData (item).GetData()
			return page


	@selectedPage.setter
	def selectedPage (self, newSelPage):
		if newSelPage == None:
			return

		item = self._pageCache[newSelPage]
		self.treeCtrl.SelectItem (item)

	
	def __set_properties(self):
		# begin wxGlade: WikiTree.__set_properties
		self.SetSize((256, 260))
		# end wxGlade

	def __do_layout(self):
		# begin wxGlade: WikiTree.__do_layout
		mainSizer = wx.FlexGridSizer(1, 1, 0, 0)
		mainSizer.Add(self.toolbar, 1, wx.EXPAND, 0)
		mainSizer.Add(self.treeCtrl, 1, wx.EXPAND, 0)
		self.SetSizer(mainSizer)
		mainSizer.AddGrowableRow(1)
		mainSizer.AddGrowableCol(0)
		# end wxGlade
	

	def treeUpdate (self, rootPage):
		"""
		Обновить дерево
		"""
		self.Unbind (wx.EVT_TREE_SEL_CHANGED, handler = self.onSelChanged)

		# Так как мы сами будем сворачивать/разворачивать узлы дерева, 
		# на эти события реагировать не надо пока строится дерево
		self.treeCtrl.Unbind (wx.EVT_TREE_ITEM_COLLAPSED, handler = self.onTreeStateChanged)
		self.treeCtrl.Unbind (wx.EVT_TREE_ITEM_EXPANDED, handler = self.onTreeStateChanged)
		
		self.treeCtrl.DeleteAllItems()
		self.imagelist.RemoveAll()
		self.defaultImageId = self.imagelist.Add (self.defaultBitmap)
		self._pageCache = {}

		if rootPage != None:
			rootname = os.path.basename (rootPage.path)
			rootItem = self.treeCtrl.AddRoot (rootname, 
					data = wx.TreeItemData (rootPage),
					image = self.defaultImageId)

			self._mountItem (rootItem, rootPage)

			self.appendChildren (rootPage, rootItem)
			self.selectedPage = rootPage.selectedPage
			self.treeCtrl.Expand (rootItem)

		self.Bind (wx.EVT_TREE_SEL_CHANGED, self.onSelChanged)
		self.treeCtrl.Bind (wx.EVT_TREE_ITEM_COLLAPSED, self.onTreeStateChanged)
		self.treeCtrl.Bind (wx.EVT_TREE_ITEM_EXPANDED, self.onTreeStateChanged)
	

	def appendChildren (self, parentPage, parentItem):
		"""
		Добавить детей в дерево
		parentPage - родительская страница, куда добавляем дочерние страницы
		parentItem - родительский элемент дерева, куда добавляем дочерние элементы
		"""
		self._pageCache[parentPage] = parentItem

		for child in parentPage.children:
			item = self.insertChild (child, parentItem)
			self._mountItem (item, child)

		self._loadExpandState (parentPage)


	def _mountItem (self, treeitem, page):
		"""
		Оформить элемент дерева в зависимости от настроек страницы (например, пометить только для чтения)
		"""
		if page.readonly:
			#font = self.treeCtrl.GetItemFont (treeitem)
			font = wx.SystemSettings.GetFont (wx.SYS_DEFAULT_GUI_FONT)
			font.SetStyle (wx.FONTSTYLE_ITALIC)
			self.treeCtrl.SetItemFont (treeitem, font)

	

	def insertChild (self, child, parentItem):
		"""
		Вставить одну дочерниюю страницу (child) в ветвь, 
		где родителем является элемент parentItem
		"""
		item = self.treeCtrl.InsertItemBefore (parentItem, 
				child.order, 
				child.title, 
				data = wx.TreeItemData(child) )

		icon = child.icon

		if icon != None:
			image = wx.Bitmap (icon)
			image.SetHeight (self.iconHeight)
			imageId = self.imagelist.Add (image)
		else:
			imageId = self.defaultImageId
			
		self.treeCtrl.SetItemImage (item, imageId)

		self.appendChildren (child, item)

		return item
	

	def _removePageItem (self, page):
		"""
		Удалить элемент, соответствующий странице
		"""
		item = self._pageCache[page]
		del self._pageCache[page]
		self.treeCtrl.Delete (item)


	def _updatePage (self, page):
		"""
		Обновить страницу (удалить из списка и добавить снова)
		"""
		# Отпишемся от обновлений страниц, чтобы не изменять выбранную страницу
		self._unbindUpdateEvents()
		self.treeCtrl.Freeze()

		self._removePageItem (page)
		item = self.insertChild (page, self._pageCache[page.parent])

		if page.root.selectedPage == page:
			# Если обновляем выбранную страницу
			self.treeCtrl.SelectItem (item)

		self.__scrollToCurrentPage()
		self.treeCtrl.Thaw()
		self._bindUpdateEvents()
	

	def __scrollToCurrentPage (self):
		"""
		Если текущая страницавылезла за пределы видимости, то прокрутить к ней
		"""
		selectedPage = Application.selectedPage
		if selectedPage == None:
			return

		item = self._pageCache[selectedPage]
		if not self.treeCtrl.IsVisible (item):
			self.treeCtrl.ScrollTo (item)
	

	def getToolbar (self, parent, id):
		imagesDir = core.system.getImagesDir()

		toolbar = wx.ToolBar (parent, id, style=wx.TB_HORIZONTAL|wx.TB_FLAT|wx.TB_DOCKABLE)

		toolbar.AddLabelTool(self.ID_MOVE_DOWN, 
				_(u"Move Page Down"), 
				wx.Bitmap(os.path.join (imagesDir, "move_down.png"),
					wx.BITMAP_TYPE_ANY),
				wx.NullBitmap, 
				wx.ITEM_NORMAL,
				_(u"Move Page Down"), 
				"")

		toolbar.AddLabelTool(self.ID_MOVE_UP, 
				_(u"Move Page Up"), 
				wx.Bitmap(os.path.join (imagesDir, "move_up.png"),
					wx.BITMAP_TYPE_ANY),
				wx.NullBitmap, 
				wx.ITEM_NORMAL,
				_(u"Move Page Up"), 
				"")
		toolbar.AddSeparator()


		toolbar.AddLabelTool(self.ID_ADD_SIBLING_PAGE,
				_(u"Add Sibling Page…"), 
				wx.Bitmap(os.path.join (imagesDir, "node-insert-next.png"),
					wx.BITMAP_TYPE_ANY),
				wx.NullBitmap, 
				wx.ITEM_NORMAL,
				_(u"Add Sibling Page…"), 
				"")

		toolbar.AddLabelTool(self.ID_ADD_CHILD_PAGE,
				_(u"Add Child Page…"), 
				wx.Bitmap(os.path.join (imagesDir, "node-insert-child.png"),
					wx.BITMAP_TYPE_ANY),
				wx.NullBitmap, 
				wx.ITEM_NORMAL,
				_(u"Add Child Page…"), 
				"")

		toolbar.AddLabelTool(self.ID_REMOVE_PAGE,
				_(u"Remove Page…"), 
				wx.Bitmap(os.path.join (imagesDir, "node-delete.png"),
					wx.BITMAP_TYPE_ANY),
				wx.NullBitmap, 
				wx.ITEM_NORMAL,
				_(u"Remove Page…"), 
				"")

		toolbar.AddSeparator()

		toolbar.AddLabelTool(self.ID_PROPERTIES_BUTTON,
				_(u"Page Properties…"), 
				wx.Bitmap(os.path.join (imagesDir, "edit.png"),
					wx.BITMAP_TYPE_ANY),
				wx.NullBitmap, 
				wx.ITEM_NORMAL,
				_(u"Page Properties…"), 
				"")


		toolbar.Realize()
		return toolbar
	

# end of class WikiTree

