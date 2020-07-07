#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author : [Awaxx] boxx1@free.fr
# License : GPLv3
# Refactoring from pySnippet-1.3 by Eduardo Aguiar (aguiar@users.sourceforge.net).

import os, sys, base64, xml.dom.minidom, string, re
import gtk, gobject, pango, gtksourceview2, subprocess

(SNIPPET_PARENT,
 SNIPPET_TITLE,
 SNIPPET_CODE,
 SNIPPET_LANGUAGE,
 SNIPPET_AUTHOR,
 SNIPPET_TAGS) = range (6)

(FOLDER_ID,
 FOLDER_NAME) = range (2)

(MENU_ITEM,
 IMAGE_MENU_ITEM,
 CHECK_MENU_ITEM,
 MENU_SEPARATOR) = range (4)

TAG_NAME = 0

__DEBUG__ = 0

def debug(str):
    if __DEBUG__:
        sys.stderr.write(str+"\n")

######################################################
## DEFINITIONS AND PROTOTYPES
class config ():
    appName         = 'AwfulSnippet'
    appVersion      = 'v0.1'
    appCopyright    = 'by [Awaxx] - boxx1@free.fr'
    appComment      = 'A wonderful snippet store.'
    appUrl          = 'http://62.210.114.224/'
    appIcon         = '/usr/share/pysnippet-1.3/icon.png'
    appFile         = '~/.pysnippet/pysnippet.xml'
    styleScheme     = 'monokai-extended'
    appFont         = 'Ubuntu mono 10'

class CodeSnippet ():
    """Import this class in your code to programmatically
       handle snippet to a given xml bed.

       **Actually you can only create and fill a new snippet file.**
    """
    def __init__ ( self ):
        self.folders  = []
        self.snippets = []
        self.tags     = []

        xml = xml.dom.minidom.getDOMImplementation ()
        self.doc  = xml.createDocument ( None, "root", None )
        self.root = self.doc.documentElement
        debug("CodeSnippet -> __init__")

    def append_folder ( self, catname, parent ):
        elm = self.doc.createElement ( 'folder' ) or None
        self.folders.append ( catname )
        elm.setAttribute ( 'id', str ( self.folders.index ( catname )+1 ) )
        elm.setAttribute ( 'name', catname )
        if parent:
            elm.setAttribute ( 'parent', str ( parent ) )
        self.root.appendChild ( elm )
        debug("CodeSnippet -> append_folder", catname)
        return self.folders.index ( catname )+1

    def append_snippet ( self, parent, title, author, language, tags, snip ):
        elm = self.doc.createElement ( 'snippet' ) or None
        self.folders.append ( [ parent,title,author,language,tags ] )
        if parent <= self.folders.__len__ ():
            elm.setAttribute ( 'parent', str ( parent ) )
            elm.setAttribute ( 'title', title )
            elm.setAttribute ( 'author', author )
            elm.setAttribute ( 'language', language )
            elm.setAttribute ( 'tags', tags )
            code = self.doc.createTextNode ( base64.b64encode ( snip ) )
            elm.appendChild ( code )
            self.root.appendChild ( elm )
            debug("CodeSnippet -> append_snippet", str ( parent ))

    def save_document( self, filename ):
        if filename:
            fp = open ( filename, "w" )
        else:
            return
        self.doc.writexml ( fp, indent="  ", newl="\n" )
        fp.close ()

class ShareSnippetDialog( gtk.MessageDialog ):
    def __init__ ( self, window, shared="Something went wrong." ):
        super ( ShareSnippetDialog, self ).__init__ (
            window,
            gtk.DIALOG_MODAL,
            gtk.MESSAGE_INFO,
            gtk.BUTTONS_NONE )
        self.set_markup(shared)
        self.show()

class RemoveSnippetDialog( gtk.MessageDialog ):
    def __init__ ( self, window ):
        super ( RemoveSnippetDialog, self ).__init__ (
            window,
            gtk.DIALOG_MODAL,
            gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_YES_NO,
            "Are you sure to remove that snippet?" )
        self.set_default_response ( gtk.RESPONSE_NO )

class RemoveFolderDialog( gtk.MessageDialog ):
    def __init__ ( self, window ):
        super ( RemoveFolderDialog, self ).__init__ (
            window,
            gtk.DIALOG_MODAL,
            gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_YES_NO,
            "Are you sure to remove that folder?" )
        self.set_default_response ( gtk.RESPONSE_NO )

class SaveDialog( gtk.MessageDialog ):
    def __init__ ( self, window ):
        super ( SaveDialog, self ).__init__ (
            window,
            gtk.DIALOG_MODAL,
            gtk.MESSAGE_QUESTION,
            gtk.BUTTONS_YES_NO,
            "Save changes?" )
        self.set_default_response ( gtk.RESPONSE_NO )

class AboutDialog ( gtk.AboutDialog ):
    def __init__ ( self, menuItem ):
        super ( AboutDialog, self ).__init__ ()
        self.set_size_request ( 300, 200 )
        self.set_position ( gtk.WIN_POS_CENTER )
        self.set_program_name ( config.appName+"\302\251" )
        self.set_version ( config.appVersion )
        self.set_copyright ( config.appCopyright )
        self.set_comments ( config.appComment )
        self.set_website ( config.appUrl )
        self.set_logo ( gtk.gdk.pixbuf_new_from_file ( config.appIcon ) )
        self.run ()
        self.destroy ()

class PropertiesDialog ( gtk.Dialog ):

  #############################################################################
  # @brief Initialize screen
  #############################################################################
  def __init__ ( self ):
    super( PropertiesDialog, self ).__init__ ( 'Snippet properties', None, gtk.DIALOG_MODAL,
                        ( gtk.STOCK_OK, gtk.RESPONSE_OK,
                         gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ) )

    self.set_default_response ( gtk.RESPONSE_CANCEL )
    self.set_size_request ( 460, 200 )
    self.set_type_hint ( gtk.gdk.WINDOW_TYPE_HINT_DIALOG )
    self.set_border_width ( 10 )

    self.vbox.set_spacing ( 5 )

    table = gtk.Table ( 4,4 )
    table.set_row_spacings ( 5 )
    table.set_col_spacings ( 5 )
    table.show ()
    self.vbox.pack_start ( table, False, False )

    label = gtk.Label ("Title")
    label.set_alignment ( 1.0, label.get_alignment ()[ 1 ] )
    label.show ()
    table.attach ( label, 0, 1, 0, 1 )

    self.title_entry = gtk.Entry ( 80 )
    self.title_entry.show ()
    table.attach ( self.title_entry, 1, 4, 0, 1 )

    label = gtk.Label ( "Author" )
    label.set_alignment ( 1.0, label.get_alignment ()[ 1 ] )
    label.show ()
    table.attach ( label, 0, 1, 1, 2 )

    self.author_entry = gtk.Entry ( 8 )
    self.author_entry.show ()
    table.attach ( self.author_entry, 1, 2, 1, 2 )

    label = gtk.Label ( "Language" )
    label.set_alignment ( 1.0, label.get_alignment ()[ 1 ] )
    label.show ()
    table.attach ( label, 2, 3, 1, 2 )

    self.language_combo = gtk.combo_box_new_text ()
    self.language_combo.show ()
    table.attach ( self.language_combo, 3, 4, 1, 2 )

    label = gtk.Label ("Tags")
    label.set_alignment ( 1.0, label.get_alignment ()[ 1 ] )
    label.show ()
    table.attach ( label, 0, 1, 2, 3 )

    self.tags_entry = gtk.Entry ( 80 )
    self.tags_entry.show ()
    table.attach ( self.tags_entry, 1, 4, 2, 3 )

    label = gtk.Label ()
    label.set_alignment ( 0.0, 0.0 )
    label.set_markup ( "<i><small>e.g: C++,STL,string,empty</small></i>" )
    label.show ()
    table.attach ( label, 1, 4, 3, 4 )

class OpenFileDialog( gtk.FileChooserDialog ):
    def __init__ ( self ):
        super ( OpenFileDialog, self ).__init__ (
        'Open file...', None,
        gtk.FILE_CHOOSER_ACTION_OPEN,
        ( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_OPEN, gtk.RESPONSE_OK )
        )
        self.set_default_response ( gtk.RESPONSE_CANCEL )
        filter = gtk.FileFilter ()
        filter.set_name ( "XML" )
        filter.add_pattern ( "*.xml" )
        self.add_filter ( filter )

class SaveFileDialog( gtk.FileChooserDialog ):
    def __init__( self ):
        super( SaveFileDialog, self ).__init__(
            "Save file...",
            None,
            gtk.FILE_CHOOSER_ACTION_SAVE,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_SAVE, gtk.RESPONSE_OK)
        )
        self.set_default_response ( gtk.RESPONSE_CANCEL )

class Menubar( gtk.MenuBar ):
    # Menu bar seem doesn't like cold start
    def __init__( self, gtkWindow ):
        super( Menubar, self ).__init__()

        # type:
        # 0 == gtk.MenuItem
        # 1 == gtk.ImageMenuItem
        # 2 == gtk.CheckMenuItem
        # 3 == gtk.SeparatorMenuItem()
        menus = [ \
            {
            'menu_label':"_File",
            'menu_items':[
                {
                    'type':IMAGE_MENU_ITEM,
                    'stockId':gtk.STOCK_OPEN,
                    'label':'Open File',
                    'binding':'<Control>O',
                    'activate': gtkWindow.open
                },
                {
                    'type':IMAGE_MENU_ITEM,
                    'stockId':gtk.STOCK_SAVE,
                    'label':'Save',
                    'binding':'<Control>S',
                    'activate': gtkWindow.save
                },
                {
                    'type':IMAGE_MENU_ITEM,
                    'stockId':gtk.STOCK_SAVE_AS,
                    'label': 'Save As',
                    'binding':'<Shift><Control>S',
                    'activate': gtkWindow.saveAs
                },
                {'type':MENU_SEPARATOR },
                {
                    'type':IMAGE_MENU_ITEM,
                    'stockId':gtk.STOCK_QUIT,
                    'label':'Quit',
                    'binding':'<Control>Q',
                    'activate': gtkWindow.mainQuit
                }
            ]},
            {
            'menu_label':"_View",
            'menu_items':[
                {
                    'type':CHECK_MENU_ITEM,
                    'label':'Show Menubar',
                    'is_active':True,
                    'activate':self.menubarView
                },
                {'type':MENU_SEPARATOR },
                {
                    'type':CHECK_MENU_ITEM,
                    'label':"Show line numbers",
                    'is_active':True,
                    'activate':sys.exit
                },
                {
                    'type':CHECK_MENU_ITEM,
                    'label':"Highlight current line",
                    'is_active':True,
                    'activate':sys.exit
                },
                {
                    'type':CHECK_MENU_ITEM,
                    'label':"Use previous properties",
                    'is_active':False,
                    'activate':gtkWindow.use_previous_properties
                },
                {
                    'type':CHECK_MENU_ITEM,
                    'label':"Auto clipboard",
                    'is_active':False,
                    'activate':gtkWindow.use_auto_clipboard
                }
            ]},
            {
            'menu_label':"_Help",
            'menu_items':[
                {
                    'type':IMAGE_MENU_ITEM,
                    'stockId':gtk.STOCK_ABOUT,
                    'label':"About",
                    'binding':None,
                    'activate':AboutDialog
                }
            ]}
        ]

        for i in menus: # root menus
            menu_label = gtk.MenuItem ( i[ 'menu_label' ] )
            menu_label_items = gtk.Menu ()
            menu_label.set_submenu ( menu_label_items )
            for n in i[ 'menu_items' ]:
                menu_item = None
                if n[ 'type' ] == MENU_SEPARATOR: # gtk.SeparatorMenuItem
                    menu_label_items.append ( gtk.SeparatorMenuItem () )
                    continue

                if n['type'] == CHECK_MENU_ITEM: # gtk.CheckMenuItem
                    menu_item = gtk.CheckMenuItem ( n[ 'label' ] )
                    if n[ 'is_active' ]:
                        menu_item.set_active ( n[ 'is_active' ] )
                    if n[ 'activate' ]:
                        menu_item.connect ( 'activate', n[ 'activate' ] )
                    menu_label_items.append ( menu_item )
                    continue

                if n[ 'type' ] == IMAGE_MENU_ITEM: # gtk.ImageMenuItem
                    if n[ 'stockId' ]:
                        menu_item = gtk.ImageMenuItem ( n[ 'stockId' ] )
                        menu_item.set_label ( n[ 'label' ] )
                        if n[ 'binding' ]:
                            menu_item.set_accel_group ( gtkWindow.accelGroup )
                            key, mod = gtk.accelerator_parse ( n[ 'binding' ] )
                            menu_item.add_accelerator ( "activate",
                                gtkWindow.accelGroup, key, mod, gtk.ACCEL_VISIBLE
                            )
                        if n[ 'activate' ]:
                            menu_item.connect ( 'activate', n[ 'activate' ] )
                    menu_label_items.append ( menu_item )
                    continue

                if n['type'] == MENU_ITEM: # gtk.MenuItem
                    menu_item = gtk.MenuItem ( n[ 'label' ] )
                    if n[ 'binding' ]:
                        key, mod = gtk.accelerator_parse ( n[ 'binding' ] )
                        menu_item.add_accelerator ( "activate",
                            gtkWindow.accelGroup, key, mod, gtk.ACCEL_VISIBLE
                        )
                    if n[ 'activate' ]:
                        menu_item.connect ( 'activate', n[ 'activate' ])
                    menu_label_items.append ( menu_item )
                    continue
            self.append ( menu_label )
        self.show ()

    def menubarView ( self, checkMenuItem ):
        if checkMenuItem.active:
            self.show ()
        else:
            self.hide ()

class Menu( gtk.Menu ):
    def __init__(self):
        super( Menu, self ).__init__()

class MenuItem( gtk.MenuItem ):
    def __init__(self, name):
        super( MenuItem, self ).__init__(name)
        self.show()

class Notebook ( gtk.Notebook ):
    def __init__ ( self ):
        super ( Notebook, self ).__init__ ()

class TreeView ( gtk.TreeView ):
    def __init__ ( self, treeModel ):
        super ( TreeView, self ).__init__ ( treeModel )
        self.set_rules_hint ( True )
        self.set_headers_visible ( False )
        #self.set_reorderable (True)
        self.selection = self.get_selection ()
        self.selection.set_mode ( gtk.SELECTION_SINGLE )

class TreeViewColumn ( gtk.TreeViewColumn ):
    def __init__ ( self ):
        super ( TreeViewColumn, self ).__init__ ()

class CellRendererPixbuf ( gtk.CellRendererPixbuf ):
    def __init__( self ):
        super ( CellRendererPixbuf, self ).__init__ ()

class CellRendererText ( gtk.CellRendererText ):
    def __init__ ( self ):
        super ( CellRendererText, self ).__init__ ()
        self.set_property ( 'editable', True )

class Frame ( gtk.Frame ):
    def __init__ ( self, shadow_type=gtk.SHADOW_NONE ):
        super ( Frame, self ).__init__ ()
        self.set_shadow_type ( shadow_type )

class ScrolledWindow ( gtk.ScrolledWindow ):
    def __init__ ( self ):
        super ( ScrolledWindow, self ).__init__ ()
        self.set_policy ( gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC )

class StyleSchemeManager ( gtksourceview2.StyleSchemeManager ):
    def __init__ ( self ):
        super ( StyleSchemeManager, self ).__init__ ()

class LanguageManager ( gtksourceview2.LanguageManager ):
    def __init__ ( self ):
        super ( LanguageManager, self ).__init__ ()
        languages = [ ( string.capitalize ( i ), i ) \
          for i in self.get_language_ids () ]

        languages.sort ()
        self.languages = [ ( 'Default', None ) ] + languages

######################################################
## FOLDERS

#############################################################################
# @brief When user selects a folder
#############################################################################
def folder_selection ( widget, *args ):
    debug("FolderView -> folder_selection")
    model, iter = widget.get_selection ().get_selected ()
    if iter:
        id = model.get_value ( iter, FOLDER_ID )
        if id:
            widget.set_folder_id ( id )
            # reset buffer only when needed
            buff = widget.textview.get_buffer()
            if buff.get_char_count():
                widget.textview.set_buffer( TextBuffer () )
            widget.textview.set_editable ( False )
            widget.textview.set_cursor_visible ( False )

#############################################################################
# @brief When user clicks right on a folder
#############################################################################
def folder_menu ( widget, event, *args ):
    debug("FolderView -> on_folder_menu")
    path = widget.get_path_at_pos(int(event.x), int(event.y))
    #if not widget.get_selection().get_selected():
    #widget.row_activated(path,widget.get_column(0))

    if event.button != 3:
        return
    if widget.get_path_at_pos(int(event.x), int(event.y)):
        # print "1: ", widget.get_path_at_pos(int(event.x), int(event.y)), "\n2: ", widget.get_path_at_pos(int(event.x), int(event.y))[0]
        # path = widget.get_path_at_pos(int(event.x), int(event.y))[0]
        context_menu( widget ,[{'name':'Add _subfolder...', 'activate':widget.add_subfolder, 'event':event},
                {'name':'_Remove folder...', 'activate':widget.remove_folder, 'event':event}] )
    else:
        context_menu( widget ,[{'name':'_Add folder...', 'activate':widget.add_folder, 'event':event}] )

    #if event.button == 3:
    #    selected = widget.get_selection ().get_selected ()[ 1 ] and True or False
    #    #widget.add_sub_menuitem.set_sensitive ( selected )
    #    #widget.remove_menuitem.set_sensitive ( selected )
    #    widget.popup_menu.popup ( None, None, None, event.button, event.time )

#############################################################################
# @brief Triggers a popup menu based on context
#############################################################################
def context_menu( widget, menuItems ):
    # this way cuz catching menu state to remove menu items... may change...
    for i in [None, Menu()]: # pretty strange to me but it's okay for now
        widget.popup_menu = i # to have dynamic parameter...
    for m in menuItems:
        menuItem = MenuItem(m['name'])
        menuItem.connect('activate', m['activate'])
        widget.popup_menu.add(menuItem)
    widget.popup_menu.popup(None, None, None, m['event'].button, m['event'].time)

class FolderView ( TreeView ):
    def __init__ ( self, ui ):
        super ( FolderView, self ).__init__ ( FolderStore () )
        debug("FolderView -> __init__")
        self.set_size_request ( 150, 200 )
        self.set_reorderable ( True )

        self.textview = ui.textview
        self.snippetstore = ui.snippetstore
        self.mainwindow = ui.mainwindow

        renderer = CellRendererText ()
        renderer.connect ( 'edited', self.edited_folder )
        tvcolumn = TreeViewColumn ()
        tvcolumn.pack_start ( renderer, True )
        tvcolumn.add_attribute ( renderer, 'text', FOLDER_NAME )

        self.append_column ( tvcolumn )
        self.connect ( 'cursor-changed', folder_selection )
        self.connect ( 'button-press-event', folder_menu )
        #self.get_selection().set_select_function(folder_selection, self)

    #############################################################################
    # @brief Set folder id
    #############################################################################
    def set_folder_id ( self, id ):
        debug("FolderView -> set_folder_id")
        self.snippetstore.set_folder ( id )
        #print "set folder", id

    #############################################################################
    # @brief Add folder
    #############################################################################
    def add_folder ( self, widget, *args ):
        debug("FolderView -> on_add_folder")
        model = self.get_model ()
        model.max_id += 1
        model.append ( None, [ model.max_id, '<NEW FOLDER>' ] )
        self.mainwindow.modified ( True )

    #############################################################################
    # @brief Add subfolder
    #############################################################################
    def add_subfolder ( self, widget, data=None ):
        debug("FolderView -> on_add_subfolder")
        model, iter = self.get_selection ().get_selected ()
        if iter:
            model.max_id += 1
            model.append ( iter, [ model.max_id, '<NEW FOLDER>' ] )
            self.mainwindow.modified ( True )

    #############################################################################
    # @brief Remove folder
    #############################################################################
    def remove_folder ( self, widget, data=None ):
        debug("FolderView -> on_remove_folder")
        model, iter = self.get_selection ().get_selected ()
        id   = model.get_value ( iter, FOLDER_ID )
        name = model.get_value ( iter, FOLDER_NAME )

        dialog = RemoveFolderDialog ( self.mainwindow )
        rc = dialog.run ()
        dialog.destroy ()

        if rc == gtk.RESPONSE_YES:
            while iter:
                parent = model.get_value ( iter, SNIPPET_PARENT )
                if parent == id:
                    iter = model.remove ( iter ) and iter or None
                else:
                    iter = model.iter_next ( iter )

            self.mainwindow.modified ( True )

    #############################################################################
    # @brief Triggered when user finished to edit column
    #############################################################################
    def edited_folder ( self, cell, path_string, new_text, *args ):
        debug("FolderView -> on_folder_edited")
        model    = self.get_model ()
        iter     = model.get_iter_from_string ( path_string )
        old_text = model.get_value ( iter, FOLDER_NAME )

        if old_text != new_text:
            model.set_value ( iter, FOLDER_NAME, new_text )
            self.mainwindow.modified ( True )

class FolderStore ( gtk.TreeStore ):
    max_id = 0
    def __init__ ( self ):
        super ( FolderStore, self ).__init__ ( gobject.TYPE_INT, gobject.TYPE_STRING )
        debug("FolderStore -> __init__")

######################################################
## TAGS

class TagView ( TreeView ):
    def __init__ ( self, ui ):
        super( TagView, self ).__init__( TagStore () )
        debug("TagView -> __init__")
        self.snippetstore = ui.snippetstore

        renderer = CellRendererText ()
        tvcolumn = TreeViewColumn ()
        tvcolumn.pack_start ( renderer, True )
        tvcolumn.add_attribute ( renderer, 'text', TAG_NAME )
        tvcolumn.set_sort_column_id ( TAG_NAME )
        self.append_column ( tvcolumn )
        #self.connect ( 'cursor-changed', tag_selection )
        self.selection.connect("changed", self.tag_selection )

    #############################################################################
    # @brief When user selects a tag
    #############################################################################
    def tag_selection (self, *args ):
        model, iter = self.get_selection ().get_selected ()
        if iter:
            name = model.get_value ( iter, TAG_NAME )
            self.snippetstore.set_tag ( name )

class TagStore ( gtk.ListStore ):
    def __init__(self):
        super( TagStore, self ).__init__( gobject.TYPE_STRING )
        debug("TagStore -> __init__")

######################################################
## SNIPPETS

#############################################################################
# @brief Snippet selection
#############################################################################
def snippet_selection ( widget, *args ):
    debug("SnippetView -> on_selection")
    #print widget, args
    f_model, f_iter = widget.get_selection ().get_selected ()
    if f_iter:
        code     = f_model.get_value ( f_iter, SNIPPET_CODE ) or ''
        language = f_model.get_value ( f_iter, SNIPPET_LANGUAGE )
        if not widget.editing:
            widget.textview.new_buffer ( code, language )

#############################################################################
# @brief When user clicks inside snippetview
#############################################################################
def snippet_menu ( widget, event, *args ):
    #print widget, event, args
    if event.button != 3:
        return
    if widget.get_path_at_pos(int(event.x), int(event.y)):
       path = widget.get_path_at_pos(int(event.x), int(event.y))[0]
       context_menu( widget, [{'name':'Remove snippet...', 'activate':widget.remove_snippet, 'event':event},
        {'name':'Properties...', 'activate':widget.properties_snippet, 'event':event}] )
    else:
        context_menu( widget, [{'name':'New snippet...', 'activate':widget.new_snippet, 'event':event}] )

class SnippetView ( TreeView ):
    editing = None              # public
    __useprevious = False       # private
    __previouslang = None
    __previousauthor = None
    __previoustags = None
    def __init__ ( self, ui ):
        super( SnippetView, self ).__init__( ui.snippetstore.filter () )
        debug("SnippetView -> __init__")
        self.textview = ui.textview
        self.mainwindow = ui.mainwindow
        self.snippetstore = ui.snippetstore

        self.connect ( 'cursor-changed', snippet_selection )
        self.connect ( 'button-press-event', snippet_menu )

        renderer = CellRendererText ()
        renderer.connect ( 'edited', self.title_snippet )

        tvcolumn = TreeViewColumn ()
        tvcolumn.pack_start ( renderer, True )
        tvcolumn.add_attribute ( renderer, 'text', SNIPPET_TITLE )
        tvcolumn.set_sort_column_id ( SNIPPET_TITLE )
        self.append_column ( tvcolumn )

    #############################################################################
    # @brief Create a new snippet
    #############################################################################
    def new_snippet ( self , *vars ):
        debug("SnippetView -> new_snippet")
        self.editing = True
        f_model  = self.snippetstore.get_filter ()
        parent   = self.snippetstore.get_folder_id ()
        title    = '<NEW SNIPPET>'
        language = ''
        code     = ''
        author   = ''
        tags     = ''

        # bug is surely around there...
        iter  = self.snippetstore.append ( [ parent, title, code, language, author, tags ] )

        f_iter  = f_model.convert_child_iter_to_iter ( iter )
        path   = f_model.get_string_from_iter ( f_iter )
        column = self.get_column ( 0 )

        self.grab_focus ()
        self.set_cursor ( path, column, True )
        self.editing = False
        self.mainwindow.modified ( True )

    #############################################################################
    # @brief Remove selected snippet
    #############################################################################
    def remove_snippet ( self, menuItem ):
        debug("SnippetView -> remove_snippet")
        #print "remove_snippet() => ", self, menuItem
        dialog = RemoveSnippetDialog ( self.mainwindow )
        rc = dialog.run ()
        dialog.hide ()
        dialog.destroy ()

        if rc == gtk.RESPONSE_YES:
            f_model, f_iter = self.get_selection ().get_selected ()
            iter = f_model.convert_iter_to_child_iter ( f_iter )
            model = f_model.get_model ()
            model.remove ( iter )

            self.mainwindow.modified ( True )
            # trigger new buff... :)
            #self.mediator.snippetview.reset_code ()

    #############################################################################
    # @brief Snippet properties
    #############################################################################
    def use_previous_props ( self ):
        debug("SnippetView -> use_previous_props")
        self.__useprevious = not self.__useprevious

    def properties_snippet ( self, menuItem ):
        debug("SnippetView -> on_properties")
        #print "properties_snippet() => ", self, menuItem
        # find selected row
        f_model, f_iter = self.get_selection ().get_selected ()
        if f_iter:
            iter  = f_model.convert_iter_to_child_iter ( f_iter )
            model = f_model.get_model ()
        else:
            #print "iter was none"
            return
        # get data
        title    = model.get_value ( iter, SNIPPET_TITLE )
        author   = model.get_value ( iter, SNIPPET_AUTHOR )
        language = model.get_value ( iter, SNIPPET_LANGUAGE )
        tags     = model.get_value ( iter, SNIPPET_TAGS )

        # build dialog
        dialog = PropertiesDialog ()
        dialog.title_entry.set_text ( title )

        languages = LanguageManager ().languages

        for idx, ( description, lang ) in enumerate ( languages ):
            dialog.language_combo.append_text ( description )
            if lang == language:
                dialog.language_combo.set_active ( idx )

        ## Sets previous language...
        ## handy when adding a lot of snippets using the same language
        ## and filling up their properties using property dialog.
        if self.__useprevious:
            if self.__previouslang:
                dialog.language_combo.set_active ( self.__previouslang )
            if self.__previousauthor:
                dialog.author_entry.set_text ( self.__previousauthor )
            if self.__previoustags:
                dialog.tags_entry.set_text ( self.__previoustags )
        else:
            dialog.author_entry.set_text ( author )
            dialog.tags_entry.set_text ( ','.join ( tags ) )

        rc = dialog.run ()

        if rc == gtk.RESPONSE_OK:
            title  = dialog.title_entry.get_text ()
            author = dialog.author_entry.get_text ()
            tags   = dialog.tags_entry.get_text ().split ( ',' ) or []

            desc, lang = languages [ dialog.language_combo.get_active () ]
            model.set_value ( iter, SNIPPET_TITLE, title )
            model.set_value ( iter, SNIPPET_AUTHOR, author )
            model.set_value ( iter, SNIPPET_LANGUAGE, lang )
            model.set_value ( iter, SNIPPET_TAGS, tags )

            self.mainwindow.modified ( True )
            code = model.get_value ( iter, SNIPPET_CODE ) or ''
            self.textview.new_buffer ( code, lang )
            self.__previouslang   = languages.index ( ( desc, lang ) )
            self.__previousauthor = author
            self.__previoustags   = ','.join ( tags )

        dialog.hide ()
        dialog.destroy ()

    #############################################################################
    # @brief Triggered when user finished to edit snippet's title
    #############################################################################
    def title_snippet ( self, cell, path_string, new_text ):
        debug("SnippetView -> on_edited")
        # treemodelfilter
        #print self, cell, path_string, new_text
        f_model  = self.get_model ()
        f_iter   = f_model.get_iter_from_string ( path_string )
        # treestore
        iter     = f_model.convert_iter_to_child_iter ( f_iter )
        model    = f_model.get_model ()
        old_text = model.get_value ( iter, SNIPPET_TITLE )

        if old_text != new_text:
            model.set_value ( iter, SNIPPET_TITLE, new_text )
            self.mainwindow.modified ( True )

        code     = model.get_value ( iter, SNIPPET_CODE ) or ''
        language = model.get_value ( iter, SNIPPET_LANGUAGE )
        if not self.editing:
            self.textview.new_buffer ( code, language )

class SnippetStore ( gtk.ListStore ):
    __folder_id = -1
    __tag       = None
    __filter    = None

    def __init__(self):
        super( SnippetStore, self ).__init__(
            gobject.TYPE_INT, # parent
            gobject.TYPE_STRING, # title
            gobject.TYPE_STRING, # code
            gobject.TYPE_STRING, # language
            gobject.TYPE_STRING, # author
            gobject.TYPE_PYOBJECT # tags
        )
        debug("SnippetStore -> __init__")
        self.set_sort_column_id ( SNIPPET_TITLE, gtk.SORT_ASCENDING )
        self.__filter = self.filter_new ()
        self.__filter.set_visible_func ( self.__do_filter )

    #############################################################################
    # @brief Set parent folder and refilter
    #############################################################################
    def set_folder ( self, folder_id ):
        debug("SnippetStore -> set_folder")
        self.__folder_id = folder_id
        self.__tag = None
        self.__filter.refilter ()

    #############################################################################
    # @brief Set parent tag and refilter
    #############################################################################
    def set_tag ( self, tag ):
        debug("SnippetStore -> set_tag")
        self.__tag = tag
        self.__folder_id = None
        self.__filter.refilter ()

    def get_folder_id ( self ):
        debug("SnippetStore -> get_folder_id")
        return self.__folder_id

    #############################################################################
    # @brief Return a TreeModelFilter
    #############################################################################
    def get_filter ( self ):
        debug("SnippetStore -> get_filter")
        return self.__filter

    #############################################################################
    # @brief Do filtering
    #############################################################################
    def __do_filter ( self, model, iter, data=None ):
        # debug("SnippetStore -> __do_filter")
        if self.__folder_id:
            return model.get_value ( iter, SNIPPET_PARENT ) == self.__folder_id
        else:
            return self.__tag in model.get_value ( iter, SNIPPET_TAGS )

    #############################################################################
    # @brief Return a TreeModelFilter
    #############################################################################
    def filter ( self ):
        debug("SnippetStore -> filter")
        return self.__filter

######################################################
## TEXTVIEW
class TextBuffer ( gtksourceview2.Buffer ):
    def __init__ ( self, code=None, lang=None ):
        super ( TextBuffer, self ).__init__ ()
        debug("TextBuffer -> __init__")
        self.set_highlight_syntax ( True )
        self.set_highlight_matching_brackets ( False )

        scheme = StyleSchemeManager ()
        style = scheme.get_scheme ( config.styleScheme )
        self.set_style_scheme ( style )
        self.lm = LanguageManager ()

        if code:
            self.show_snippet ( code, lang )

    #############################################################################
    # @brief Set text and language
    #############################################################################
    def show_snippet ( self, code, language=None ):
        debug("TextBuffer -> show_snippet")
        if language:
            language = self.lm.get_language ( language )

        self.begin_not_undoable_action ()

        if language:
            self.set_highlight_syntax ( True )
            self.set_language ( language )
        else:
            debug('No language selected.')
            self.set_highlight_syntax ( False )

        self.set_text ( code.strip () )
        self.end_not_undoable_action ()
        self.set_modified ( False )

#############################################################################
# @brief Populate(insert) textview popup menu
#############################################################################
def populate_menu ( widget, popup, data=None ):
    debug("populate_menu")
    item = gtk.MenuItem ( 'Share snippet' )
    item.show ()
    popup.append ( item )
    item.connect ( 'activate', widget.share_snippet )

    item = gtk.MenuItem ( 'Highlight' )
    item.show ()
    popup.append (item)
    menu = gtk.Menu ()
    menu.show ()
    item.set_submenu ( menu )
    group = None
    for desc, language in LanguageManager ().languages:
        item = gtk.RadioMenuItem ( group, desc )
        # activate item before setting the event...
        item.set_active ( language == widget.language )
        item.connect ( 'activate', widget.on_syntax_selection, language )
        item.show ()
        menu.append ( item )
    if not group: group = item

class TextView ( gtksourceview2.View ):
    language = None
    clipboard = False
    def __init__ ( self, ui ):
        super ( TextView, self ).__init__ ( TextBuffer () )
        debug("TextView -> __init__")
        self.ui = ui
        self.set_indent_width ( 4 )
        self.set_editable ( False )
        self.set_cursor_visible ( False )
        self.set_left_margin ( 5 )
        self.set_right_margin ( 5 )
        self.set_highlight_current_line ( True )
        self.set_show_line_numbers ( True )
        self.set_indent_on_tab ( True )
        self.set_auto_indent ( True )
        self.set_right_margin_position ( 80 )
        self.set_show_right_margin ( True )
        self.set_insert_spaces_instead_of_tabs ( True )

        self.set_draw_spaces ( gtksourceview2.DRAW_SPACES_SPACE|gtksourceview2.DRAW_SPACES_TAB )
        self.modify_font ( pango.FontDescription ( config.appFont ) )
        self.gtkSourceGutter = self.get_gutter ( gtk.TEXT_WINDOW_LEFT )
        self.connect ( 'populate-popup', populate_menu )

    #############################################################################
    # @brief Opens up a new buffer
    #############################################################################
    def new_buffer( self, code, lang ):
        debug("TextView -> new_buffer")
        self.set_buffer ( TextBuffer ( code, lang ) )
        self.language = lang
        self.get_buffer ().connect ( 'changed', self.on_modified )
        self.set_editable ( True )
        self.set_cursor_visible ( True )
        if self.clipboard:
            self.copy_to_clipboard ()

    #############################################################################
    # @brief Occurs when buffer is modified
    #############################################################################
    def on_modified ( self, buffer, data=None ):
        debug("TextView -> on_modified")
        start, end = buffer.get_bounds ()
        # sets snippet_code to the selected snippet
        self.ui.set_snippet_code ( buffer.get_text ( start, end ) )

    #############################################################################
    # @brief Change syntax highlight property
    #############################################################################
    def on_syntax_selection ( self, menuItem, data=None ):
        debug("TextView -> on_syntax_selection")
        self.language = data
        f_model, f_iter = self.ui.snippetview.get_selection ().get_selected ()
        if f_iter:
            iter = f_model.convert_iter_to_child_iter ( f_iter )
            model = f_model.get_model ()
            code = model.get_value ( iter, SNIPPET_CODE )
        self.new_buffer ( code, data )
        self.ui.mainwindow.modified ( True )

    #############################################################################
    # @brief Switch auto clipboard
    #############################################################################
    def use_auto_clipboard ( self ):
        debug("SnippetView -> use_previous_props")
        self.clipboard = not self.clipboard

    #############################################################################
    # @brief Copy code to clipboard
    #############################################################################
    def copy_to_clipboard ( self, ret=None ):
        debug("TextView -> copy_to_clipboard")
        buff = self.get_buffer()
        start, end = buff.get_bounds ()
        code = buff.get_text ( start, end )
        if ret: return code
        clipboard = gtk.clipboard_get ( gtk.gdk.SELECTION_CLIPBOARD )
        clipboard.set_text ( code.strip () )

    #############################################################################
    # @brief Populate(insert) textview popup menu
    #############################################################################
    def share_snippet ( self , menuItem ):
        code = self.copy_to_clipboard ( True )
        snippet = open ('/tmp/_snippet', 'w')
        snippet.write ( code )
        snippet.close ()
        
        proc = subprocess.Popen(
        'curl --user-agent "curl/0.00.0" -F"file=@/tmp/_snippet" https://0x0.st',
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
        )
        out_val, err_val = proc.communicate()
        os.unlink('/tmp/_snippet')
        if out_val:
            clipboard = gtk.clipboard_get ( gtk.gdk.SELECTION_CLIPBOARD )
            clipboard.set_text ( out_val.strip () )
            ShareSnippetDialog( self.ui.mainwindow, out_val )


######################################################
## MAIN
class UserInterface ( gtk.VBox ):
    __folder_id = None
    __tag = None

    def __init__ ( self, gtkWindow ):
        super ( UserInterface, self ).__init__ ( False, 1 )
        debug("UserInterface -> __init__")
        self.mainwindow          = gtkWindow
        self.snippetstore        = SnippetStore ()

        self.textview            = TextView ( self )
        self.snippetview         = SnippetView ( self )
        self.folderview          = FolderView ( self )
        self.tagview             = TagView ( self )

        self.load()

        self.pack_start ( Menubar ( self.mainwindow ),
            expand=False, fill=True, padding=0 )

        # vertical pane
        vpaned = gtk.VPaned ()
        vpaned.set_border_width ( 2 )
        self.pack_start ( vpaned )

        # 1 vertical pane
        hpaned = gtk.HPaned ()
        vpaned.add1 ( hpaned )

        # 1 horizontal widget
        frame = Frame ()
        hpaned.add1 ( frame )
        sw = ScrolledWindow ()
        sw.add ( self.folderview )
        notebook = Notebook()
        notebook.connect ( 'switch-page', self.notebook_switch )
        notebook.append_page ( sw, gtk.Label ('Folders') )
        sw = ScrolledWindow ()
        sw.add ( self.tagview )
        notebook.append_page ( sw, gtk.Label ('Tags') )
        frame.add ( notebook )

        # 2 horizontal widget
        frame = Frame ( gtk.SHADOW_ETCHED_IN )
        hpaned.add2 ( frame )
        sw = ScrolledWindow ()
        sw.add ( self.snippetview )
        frame.add ( sw )

        # 2 vertical pane
        frame = Frame ( gtk.SHADOW_ETCHED_IN )
        vpaned.add2 ( frame )
        sw = ScrolledWindow ()
        frame.add ( sw )
        sw.add ( self.textview )

    def notebook_switch ( self, notebook, gpointer, page_num ):
        debug("UserInterface -> notebook_switch")
        buff = self.textview.get_buffer()
        if buff.get_char_count():
            self.textview.set_buffer( TextBuffer () )

        self.textview.set_editable ( False )
        self.textview.set_cursor_visible ( False )
        if page_num == 0:
            model, iter = self.folderview.get_selection ().get_selected ()
            if iter:
                id = model.get_value ( iter, FOLDER_ID )
                self.snippetstore.set_folder ( id )
        else:
            model, iter = self.tagview.get_selection ().get_selected ()
            if iter:
                name = model.get_value ( iter, TAG_NAME )
                self.snippetstore.set_tag ( name )

    #############################################################################
    # @brief Set code for current snippet
    #############################################################################
    def set_snippet_code ( self, code ):
        debug("UserInterface -> set_snippet_code")
        f_model, f_iter = self.snippetview.get_selection ().get_selected ()
        if f_iter:
            iter = f_model.convert_iter_to_child_iter ( f_iter )
            model = f_model.get_model ()
            previous_code = model.get_value ( iter, SNIPPET_CODE )
            if previous_code != code:
                model.set_value ( iter, SNIPPET_CODE, code )
                self.mainwindow.modified ( True )

    #############################################################################
    # @brief Set language for current snippet
    #############################################################################
    def set_snippet_language ( self, language ):
        debug("UserInterface -> set_snippet_language")
        f_model, f_iter = self.snippetview.get_selection ().get_selected ()
        if f_iter:
            iter = f_model.convert_iter_to_child_iter ( f_iter )
            model = f_model.get_model ()
            model.set_value ( iter, SNIPPET_LANGUAGE, language )

    #############################################################################
    # @brief Load snippet definition file (XML) and populate models
    # @feel A lil greedy but heh... can change at any time :)
    #############################################################################
    def load ( self, filename=None ):
        debug("UserInterface -> load")
        self.folders  = self.folderview.get_model ()
        self.tags     = self.tagview.get_model ()
        self.snippets = self.snippetstore

        doc = None
        self.snippets.clear ()
        self.folders.clear ()
        self.tags.clear ()

        snippetdir = re.sub( '/pysnippet.xml$', '', config.appFile )

        if filename:
            doc = xml.dom.minidom.parse ( filename )

        if not doc and not os.path.exists( os.path.expanduser( snippetdir ) ):
            os.mkdir( os.path.expanduser( snippetdir ) )
            self.defaultXml()

        if not doc:
            try:
                doc = xml.dom.minidom.parse ( os.path.expanduser( config.appFile ) )
            except Exception, e:
                raise e

        nodes   = {}
        tag_set = set ()

        # folders
        for node in doc.getElementsByTagName ( 'folder' ):
            id     = int (node.getAttribute ( 'id' ) )
            parent = int (node.getAttribute ( 'parent' ) or '-1' )
            name   = node.getAttribute ( 'name' )

            if parent == -1:
                iter = self.folders.append ( None, [ id, name ] )
            else:
                iter = self.folders.append ( nodes [ parent ], [ id, name ] )

            nodes [ id ] = iter
            self.folders.max_id = max ( self.folders.max_id, id )

        # snippets
        for node in doc.getElementsByTagName ( 'snippet' ):
            parent   = int ( node.getAttribute ( 'parent' ) )
            title    = node.getAttribute ( 'title' )
            language = node.getAttribute ( 'language' )
            tags     = node.getAttribute ( 'tags' )
            author   = node.getAttribute ( 'author' )
            code     = base64.b64decode ( node.childNodes[ 0 ].data )

            if tags:
                tags = tags.split ( ',' )
                tag_set.update ( tags )
            else:
                tags = []

            self.snippets.append ( [ parent, title, code, language, author, tags ] )

        # tags
        tags = list ( tag_set )
        tags.sort ()

        for tag in tags:
            self.tags.append ( [ tag ] )

    #############################################################################
    # @brief create a default snippet definition file (XML)
    #############################################################################
    def defaultXml ( self ):
        debug("UserInterface -> defaultXml")
        impl = xml.dom.minidom.getDOMImplementation ()
        doc  = impl.createDocument (None, "root", None)
        root = doc.documentElement
        elm = doc.createElement ('folder')
        elm.setAttribute ('id', "1")
        elm.setAttribute ('name', "my first snippet")
        root.appendChild (elm)
        elm = doc.createElement ('snippet') or None
        elm.setAttribute ('parent', "1")
        elm.setAttribute ('title', "python import")
        elm.setAttribute ('author', "my name")
        elm.setAttribute ('language', "python")
        elm.setAttribute ('tags', 'python,sys')
        code = doc.createTextNode (base64.b64encode ('import sys'))
        elm.appendChild (code)
        root.appendChild (elm)
        # finally write the default file
        fp = open ( os.path.expanduser( config.appFile ), "w" )
        doc.writexml (fp, indent="  ", newl="\n")
        fp.close ()

    #############################################################################
    # @brief Save model
    #############################################################################
    def save ( self, filename=None ):
        debug("UserInterface -> save")
        impl = xml.dom.minidom.getDOMImplementation ()
        doc  = impl.createDocument ( None, "root", None )
        root = doc.documentElement

        # folders, see load()
        self.folders.foreach ( self.__save_folders, root )

        # snippets
        for parent, title, code, language, author, tags in self.snippets:
            slot = doc.createElement ( 'snippet' )
            slot.setAttribute ( 'parent', str (parent) )
            slot.setAttribute ( 'title', title )
            slot.setAttribute ( 'author', author )

            if language:
                slot.setAttribute ( 'language', language )

            if tags:
                slot.setAttribute ( 'tags', ','.join ( tags ) )

            if code:
                textnode = doc.createTextNode ( base64.b64encode ( code ) )
                slot.appendChild ( textnode )

            root.appendChild ( slot )

        # save to file
        fp = None
        try:
            if filename:
                fp = open ( filename, "w" )
            else:
                fp = open ( os.path.expanduser( config.appFile ), "w" )
            doc.writexml ( fp, indent="  ", newl="\n" )
        except Exception, e:
            print e

        fp.close ()
        self.mainwindow.modified ( False )

    #############################################################################
    # @brief Save a folder
    #############################################################################
    def __save_folders ( self, model, path, iter, root ):
        debug("UserInterface -> __save_folders")
        doc   = root.ownerDocument
        piter = model.iter_parent ( iter )

        slot = doc.createElement ( 'folder' )
        slot.setAttribute ( 'id', str (model.get_value ( iter, FOLDER_ID ) ) )
        slot.setAttribute ( 'name', model.get_value ( iter, FOLDER_NAME ) )
        if piter:
            slot.setAttribute ( 'parent', str ( model.get_value ( piter, FOLDER_ID ) ) )

        root.appendChild ( slot )

class AwfulSnippet ( gtk.Window ):
    __modified = False
    def use_previous_properties ( self, ImageMenuItem=None ):
        debug("AwfulSnippet -> use_previous_properties")
        self.ui.snippetview.use_previous_props()

    def use_auto_clipboard ( self, ImageMenuItem=None ):
        debug("AwfulSnippet -> use_auto_clipboard")
        self.ui.textview.use_auto_clipboard()

    def mainQuit ( self, widget ):
        debug("AwfulSnippet -> mainQuit")
        if self.__modified:
            dialog = SaveDialog ( self )
            rc = dialog.run ()
            dialog.destroy ()

            if rc == gtk.RESPONSE_YES:
                self.ui.save ()

        self.hide_all ()
        gtk.main_quit ()

    #############################################################################
    # @brief Triggered by menu or ctrl+s
    def save ( self, widget ):
        debug("AwfulSnippet -> save")
        self.ui.save ()

    #############################################################################
    # @brief Triggered by menu or ctrl+shift+s
    def saveAs ( self, widget ):
        debug("AwfulSnippet -> saveAs")
        dialog = SaveFileDialog ()
        response = dialog.run ()

        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename ()
            if filename:
                self.ui.save ( filename )

        dialog.hide ()
        dialog.destroy ()

    #############################################################################
    # @brief Triggered by menu or ctrl+o
    def open ( self, widget ):
        debug("AwfulSnippet -> open")
        dialog = OpenFileDialog ()
        response = dialog.run ()
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename ()
            if os.path.isdir ( filename ):
                return
            if filename:
                self.ui.load ( filename )

        dialog.hide ()
        dialog.destroy ()

    #############################################################################
    # @brief Triggered whenever something change.
    def modified ( self, modified ):
        debug("AwfulSnippet -> modified")
        self.__modified = modified
        if modified:
            self.set_title ( config.appName+" - modified" )
        else:
            self.set_title ( config.appName )

    def __init__ (self):
        super ( AwfulSnippet, self ).__init__ ( gtk.WINDOW_TOPLEVEL )
        self.set_title ( config.appName )

        self.accelGroup = gtk.AccelGroup ()
        self.add_accel_group ( self.accelGroup )
        try:
            self.set_icon_from_file ( config.appIcon )
        except Exception, e:
            print e.message

        self.connect ( "destroy", self.mainQuit )
        self.set_size_request ( 800, 600 )
        self.set_position ( gtk.WIN_POS_CENTER )

        debug("AwfulSnippet -> __init__")

        self.ui = UserInterface ( self )
        self.add ( self.ui )

        self.show_all ()

if __name__ == '__main__':
    app = AwfulSnippet ()
    gtk.main ()
