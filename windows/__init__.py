# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 4.2.1-111-g5faebfea)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

from .components.dataview import TableIndexesDataViewCtrl
from .components.dataview import TableForeignKeysDataViewCtrl
from .components.dataview import TableColumnsDataViewCtrl
from .components.dataview import TableRecordsDataViewCtrl
import wx
import wx.xrc
import wx.dataview
import wx.stc

import gettext
_ = gettext.gettext

###########################################################################
## Class SessionManagerView
###########################################################################

class SessionManagerView ( wx.Dialog ):

	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = _(u"Session Manager"), pos = wx.DefaultPosition, size = wx.Size( 800,600 ), style = wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.RESIZE_BORDER )

		self.SetSizeHints( wx.Size( -1,-1 ), wx.DefaultSize )

		bSizer34 = wx.BoxSizer( wx.VERTICAL )

		self.m_splitter3 = wx.SplitterWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_LIVE_UPDATE )
		self.m_splitter3.Bind( wx.EVT_IDLE, self.m_splitter3OnIdle )
		self.m_splitter3.SetMinimumPaneSize( 250 )

		self.m_panel16 = wx.Panel( self.m_splitter3, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,-1 ), wx.TAB_TRAVERSAL )
		bSizer35 = wx.BoxSizer( wx.VERTICAL )

		self.session_tree_ctrl = wx.dataview.TreeListCtrl( self.m_panel16, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.dataview.TL_DEFAULT_STYLE )
		self.session_tree_ctrl.AppendColumn( _(u"Name"), wx.COL_WIDTH_DEFAULT, wx.ALIGN_LEFT, wx.COL_RESIZABLE )
		self.session_tree_ctrl.AppendColumn( _(u"Last connection"), wx.COL_WIDTH_DEFAULT, wx.ALIGN_LEFT, wx.COL_RESIZABLE )
		self.m_menu5 = wx.Menu()
		self.m_menuItem4 = wx.MenuItem( self.m_menu5, wx.ID_ANY, _(u"New directory"), wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu5.Append( self.m_menuItem4 )

		self.m_menuItem5 = wx.MenuItem( self.m_menu5, wx.ID_ANY, _(u"New Session"), wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu5.Append( self.m_menuItem5 )

		self.m_menu5.AppendSeparator()

		self.m_menuItem10 = wx.MenuItem( self.m_menu5, wx.ID_ANY, _(u"Import"), wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu5.Append( self.m_menuItem10 )

		self.session_tree_ctrl.Bind( wx.EVT_RIGHT_DOWN, self.session_tree_ctrlOnContextMenu )


		bSizer35.Add( self.session_tree_ctrl, 1, wx.EXPAND | wx.ALL, 5 )


		self.m_panel16.SetSizer( bSizer35 )
		self.m_panel16.Layout()
		bSizer35.Fit( self.m_panel16 )
		self.m_panel17 = wx.Panel( self.m_splitter3, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer36 = wx.BoxSizer( wx.VERTICAL )

		self.m_notebook4 = wx.Notebook( self.m_panel17, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.NB_FIXEDWIDTH )
		self.panel_session = wx.Panel( self.m_notebook4, wx.ID_ANY, wx.DefaultPosition, wx.Size( 600,-1 ), wx.BORDER_NONE|wx.TAB_TRAVERSAL )
		self.panel_session.SetMinSize( wx.Size( 600,-1 ) )

		bSizer12 = wx.BoxSizer( wx.VERTICAL )

		bSizer1211 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText211 = wx.StaticText( self.panel_session, wx.ID_ANY, _(u"Session Name"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText211.Wrap( -1 )

		bSizer1211.Add( self.m_staticText211, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.name = wx.TextCtrl( self.panel_session, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer1211.Add( self.name, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


		bSizer12.Add( bSizer1211, 0, wx.EXPAND, 5 )

		bSizer13 = wx.BoxSizer( wx.HORIZONTAL )

		bSizer13.SetMinSize( wx.Size( -1,0 ) )
		self.m_staticText2 = wx.StaticText( self.panel_session, wx.ID_ANY, _(u"Connection Type"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText2.Wrap( -1 )

		bSizer13.Add( self.m_staticText2, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		engineChoices = []
		self.engine = wx.Choice( self.panel_session, wx.ID_ANY, wx.DefaultPosition, wx.Size( 400,-1 ), engineChoices, 0 )
		self.engine.SetSelection( 0 )
		bSizer13.Add( self.engine, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


		bSizer12.Add( bSizer13, 0, wx.EXPAND, 5 )

		bSizer51 = wx.BoxSizer( wx.VERTICAL )

		self.panel_credentials = wx.Panel( self.panel_session, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer48 = wx.BoxSizer( wx.VERTICAL )

		bSizer121 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText21 = wx.StaticText( self.panel_credentials, wx.ID_ANY, _(u"Host Name / IP"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText21.Wrap( -1 )

		bSizer121.Add( self.m_staticText21, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.hostname = wx.TextCtrl( self.panel_credentials, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer121.Add( self.hostname, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


		bSizer48.Add( bSizer121, 0, wx.EXPAND, 5 )

		bSizer122 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText22 = wx.StaticText( self.panel_credentials, wx.ID_ANY, _(u"Username"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText22.Wrap( -1 )

		bSizer122.Add( self.m_staticText22, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.username = wx.TextCtrl( self.panel_credentials, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer122.Add( self.username, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


		bSizer48.Add( bSizer122, 0, wx.EXPAND, 5 )

		bSizer1221 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText221 = wx.StaticText( self.panel_credentials, wx.ID_ANY, _(u"Password"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText221.Wrap( -1 )

		bSizer1221.Add( self.m_staticText221, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.password = wx.TextCtrl( self.panel_credentials, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_PASSWORD )
		bSizer1221.Add( self.password, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


		bSizer48.Add( bSizer1221, 0, wx.EXPAND, 5 )

		bSizer12211 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText2211 = wx.StaticText( self.panel_credentials, wx.ID_ANY, _(u"Port"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText2211.Wrap( -1 )

		bSizer12211.Add( self.m_staticText2211, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.port = wx.SpinCtrl( self.panel_credentials, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 65536, 3306 )
		bSizer12211.Add( self.port, 0, wx.ALL, 5 )


		bSizer48.Add( bSizer12211, 0, wx.EXPAND, 5 )


		self.panel_credentials.SetSizer( bSizer48 )
		self.panel_credentials.Layout()
		bSizer48.Fit( self.panel_credentials )
		bSizer51.Add( self.panel_credentials, 0, wx.EXPAND | wx.ALL, 0 )

		self.panel_source = wx.Panel( self.panel_session, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.panel_source.Hide()

		bSizer52 = wx.BoxSizer( wx.VERTICAL )

		bSizer1212 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText212 = wx.StaticText( self.panel_source, wx.ID_ANY, _(u"Filename"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText212.Wrap( -1 )

		bSizer1212.Add( self.m_staticText212, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.filename = wx.FilePickerCtrl( self.panel_source, wx.ID_ANY, wx.EmptyString, _(u"Select a file"), _(u"Database (*.db;*.db3;*.sdb;*.s3db;*.sqlite;*.sqlite3)|*.db;*.db3;*.sdb;*.s3db;*.sqlite;*.sqlite3"), wx.DefaultPosition, wx.DefaultSize, wx.FLP_CHANGE_DIR|wx.FLP_USE_TEXTCTRL )
		bSizer1212.Add( self.filename, 1, wx.ALL, 5 )


		bSizer52.Add( bSizer1212, 0, wx.EXPAND, 0 )


		self.panel_source.SetSizer( bSizer52 )
		self.panel_source.Layout()
		bSizer52.Fit( self.panel_source )
		bSizer51.Add( self.panel_source, 0, wx.EXPAND | wx.ALL, 0 )


		bSizer12.Add( bSizer51, 0, wx.EXPAND, 0 )

		bSizer122111 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText22111 = wx.StaticText( self.panel_session, wx.ID_ANY, _(u"Comments"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText22111.Wrap( -1 )

		bSizer122111.Add( self.m_staticText22111, 0, wx.ALL, 5 )

		self.comments = wx.TextCtrl( self.panel_session, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,200 ), wx.TE_MULTILINE )
		bSizer122111.Add( self.comments, 1, wx.ALL|wx.EXPAND, 5 )


		bSizer12.Add( bSizer122111, 0, wx.EXPAND, 5 )


		self.panel_session.SetSizer( bSizer12 )
		self.panel_session.Layout()
		self.m_notebook4.AddPage( self.panel_session, _(u"Settings"), False )
		self.m_panel18 = wx.Panel( self.m_notebook4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer361 = wx.BoxSizer( wx.VERTICAL )

		bSizer37 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText15 = wx.StaticText( self.m_panel18, wx.ID_ANY, _(u"Created at:"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText15.Wrap( -1 )

		self.m_staticText15.SetMinSize( wx.Size( 200,-1 ) )

		bSizer37.Add( self.m_staticText15, 0, wx.ALL, 5 )

		self.created_at = wx.StaticText( self.m_panel18, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.created_at.Wrap( -1 )

		bSizer37.Add( self.created_at, 0, wx.ALL, 5 )


		bSizer361.Add( bSizer37, 0, wx.EXPAND, 5 )

		bSizer371 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText151 = wx.StaticText( self.m_panel18, wx.ID_ANY, _(u"Last connection:"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText151.Wrap( -1 )

		self.m_staticText151.SetMinSize( wx.Size( 200,-1 ) )

		bSizer371.Add( self.m_staticText151, 0, wx.ALL, 5 )

		self.last_connection_at = wx.StaticText( self.m_panel18, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.last_connection_at.Wrap( -1 )

		bSizer371.Add( self.last_connection_at, 0, wx.ALL, 5 )


		bSizer361.Add( bSizer371, 0, wx.EXPAND, 5 )

		bSizer3711 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText1511 = wx.StaticText( self.m_panel18, wx.ID_ANY, _(u"Successful connections:"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1511.Wrap( -1 )

		self.m_staticText1511.SetMinSize( wx.Size( 200,-1 ) )

		bSizer3711.Add( self.m_staticText1511, 0, wx.ALL, 5 )

		self.successful_connections = wx.StaticText( self.m_panel18, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.successful_connections.Wrap( -1 )

		bSizer3711.Add( self.successful_connections, 0, wx.ALL, 5 )


		bSizer361.Add( bSizer3711, 0, wx.EXPAND, 5 )

		bSizer37111 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText15111 = wx.StaticText( self.m_panel18, wx.ID_ANY, _(u"Unsuccessful connections:"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText15111.Wrap( -1 )

		self.m_staticText15111.SetMinSize( wx.Size( 200,-1 ) )

		bSizer37111.Add( self.m_staticText15111, 0, wx.ALL, 5 )

		self.unsuccessful_connections = wx.StaticText( self.m_panel18, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.unsuccessful_connections.Wrap( -1 )

		bSizer37111.Add( self.unsuccessful_connections, 0, wx.ALL, 5 )


		bSizer361.Add( bSizer37111, 0, wx.EXPAND, 5 )


		self.m_panel18.SetSizer( bSizer361 )
		self.m_panel18.Layout()
		bSizer361.Fit( self.m_panel18 )
		self.m_notebook4.AddPage( self.m_panel18, _(u"Statistics"), False )

		bSizer36.Add( self.m_notebook4, 1, wx.ALL|wx.EXPAND, 5 )


		self.m_panel17.SetSizer( bSizer36 )
		self.m_panel17.Layout()
		bSizer36.Fit( self.m_panel17 )
		self.m_splitter3.SplitVertically( self.m_panel16, self.m_panel17, 250 )
		bSizer34.Add( self.m_splitter3, 1, wx.EXPAND, 5 )

		self.m_staticline4 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer34.Add( self.m_staticline4, 0, wx.EXPAND | wx.ALL, 5 )

		bSizer28 = wx.BoxSizer( wx.HORIZONTAL )

		bSizer301 = wx.BoxSizer( wx.HORIZONTAL )

		self.btn_create = wx.Button( self, wx.ID_ANY, _(u"Create"), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer301.Add( self.btn_create, 0, wx.ALL|wx.BOTTOM, 5 )

		self.btn_save = wx.Button( self, wx.ID_ANY, _(u"Save"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.btn_save.Enable( False )

		bSizer301.Add( self.btn_save, 0, wx.ALL, 5 )

		self.btn_delete = wx.Button( self, wx.ID_ANY, _(u"Delete"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.btn_delete.Enable( False )

		bSizer301.Add( self.btn_delete, 0, wx.ALL, 5 )


		bSizer28.Add( bSizer301, 1, wx.EXPAND, 5 )

		bSizer29 = wx.BoxSizer( wx.HORIZONTAL )

		self.btn_cancel = wx.Button( self, wx.ID_ANY, _(u"Cancel"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.btn_cancel.Hide()

		bSizer29.Add( self.btn_cancel, 0, wx.ALL, 5 )

		self.btn_open = wx.Button( self, wx.ID_ANY, _(u"Open"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.btn_open.Enable( False )

		bSizer29.Add( self.btn_open, 0, wx.ALL, 5 )


		bSizer28.Add( bSizer29, 0, wx.EXPAND, 5 )


		bSizer34.Add( bSizer28, 0, wx.EXPAND, 0 )


		self.SetSizer( bSizer34 )
		self.Layout()

		self.Centre( wx.BOTH )

		# Connect Events
		self.Bind( wx.EVT_CLOSE, self.on_close )
		self.Bind( wx.EVT_MENU, self.on_new_directory, id = self.m_menuItem4.GetId() )
		self.Bind( wx.EVT_MENU, self.on_new_session, id = self.m_menuItem5.GetId() )
		self.Bind( wx.EVT_MENU, self.on_import, id = self.m_menuItem10.GetId() )
		self.engine.Bind( wx.EVT_CHOICE, self.on_choice_engine )
		self.btn_create.Bind( wx.EVT_BUTTON, self.on_create )
		self.btn_save.Bind( wx.EVT_BUTTON, self.on_save )
		self.btn_delete.Bind( wx.EVT_BUTTON, self.on_delete )
		self.btn_open.Bind( wx.EVT_BUTTON, self.on_open )

	def __del__( self ):
		pass


	# Virtual event handlers, override them in your derived class
	def on_close( self, event ):
		event.Skip()

	def on_new_directory( self, event ):
		event.Skip()

	def on_new_session( self, event ):
		event.Skip()

	def on_import( self, event ):
		event.Skip()

	def on_choice_engine( self, event ):
		event.Skip()

	def on_create( self, event ):
		event.Skip()

	def on_save( self, event ):
		event.Skip()

	def on_delete( self, event ):
		event.Skip()

	def on_open( self, event ):
		event.Skip()

	def m_splitter3OnIdle( self, event ):
		self.m_splitter3.SetSashPosition( 250 )
		self.m_splitter3.Unbind( wx.EVT_IDLE )

	def session_tree_ctrlOnContextMenu( self, event ):
		self.session_tree_ctrl.PopupMenu( self.m_menu5, event.GetPosition() )


###########################################################################
## Class Settings
###########################################################################

class Settings ( wx.Dialog ):

	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = _(u"Settings"), pos = wx.DefaultPosition, size = wx.Size( 800,600 ), style = wx.DEFAULT_DIALOG_STYLE )

		self.SetSizeHints( wx.Size( 800,600 ), wx.DefaultSize )

		bSizer63 = wx.BoxSizer( wx.VERTICAL )

		self.m_notebook4 = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.locales = wx.Panel( self.m_notebook4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer65 = wx.BoxSizer( wx.VERTICAL )

		bSizer64 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText27 = wx.StaticText( self.locales, wx.ID_ANY, _(u"Language"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText27.Wrap( -1 )

		bSizer64.Add( self.m_staticText27, 0, wx.ALL, 5 )

		m_choice5Choices = [ _(u"English"), _(u"Italian"), _(u"French") ]
		self.m_choice5 = wx.Choice( self.locales, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice5Choices, 0|wx.BORDER_NONE )
		self.m_choice5.SetSelection( 0 )
		bSizer64.Add( self.m_choice5, 1, wx.ALL, 5 )


		bSizer65.Add( bSizer64, 1, wx.EXPAND, 5 )


		self.locales.SetSizer( bSizer65 )
		self.locales.Layout()
		bSizer65.Fit( self.locales )
		self.m_notebook4.AddPage( self.locales, _(u"Locale"), False )

		bSizer63.Add( self.m_notebook4, 1, wx.EXPAND | wx.ALL, 5 )


		self.SetSizer( bSizer63 )
		self.Layout()

		self.Centre( wx.BOTH )

	def __del__( self ):
		pass


###########################################################################
## Class MainFrameView
###########################################################################

class MainFrameView ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = _(u"PeterSQL"), pos = wx.DefaultPosition, size = wx.Size( 1024,762 ), style = wx.DEFAULT_FRAME_STYLE|wx.MAXIMIZE_BOX|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.Size( 800,600 ), wx.DefaultSize )

		self.m_menubar2 = wx.MenuBar( 0 )
		self.m_menu2 = wx.Menu()
		self.m_menubar2.Append( self.m_menu2, _(u"File") )

		self.m_menu4 = wx.Menu()
		self.m_menubar2.Append( self.m_menu4, _(u"About") )

		self.SetMenuBar( self.m_menubar2 )

		self.m_toolBar1 = self.CreateToolBar( wx.TB_HORIZONTAL, wx.ID_ANY )
		self.m_tool5 = self.m_toolBar1.AddTool( wx.ID_ANY, _(u"Open session manager"), wx.Bitmap( u"icons/16x16/server_connect.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

		self.m_tool4 = self.m_toolBar1.AddTool( wx.ID_ANY, _(u"Disconnect from server"), wx.Bitmap( u"icons/16x16/disconnect.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

		self.m_toolBar1.AddSeparator()

		self.database_refresh = self.m_toolBar1.AddTool( wx.ID_ANY, _(u"tool"), wx.Bitmap( u"icons/16x16/database_refresh.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Refresh"), _(u"Refresh"), None )

		self.m_toolBar1.AddSeparator()

		self.database_add = self.m_toolBar1.AddTool( wx.ID_ANY, _(u"Add"), wx.Bitmap( u"icons/16x16/database_add.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

		self.database_delete = self.m_toolBar1.AddTool( wx.ID_ANY, _(u"Add"), wx.Bitmap( u"icons/16x16/database_delete.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

		self.m_toolBar1.Realize()

		bSizer19 = wx.BoxSizer( wx.VERTICAL )

		self.m_panel13 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer21 = wx.BoxSizer( wx.VERTICAL )

		self.m_splitter51 = wx.SplitterWindow( self.m_panel13, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_3D|wx.SP_LIVE_UPDATE )
		self.m_splitter51.SetSashGravity( 1 )
		self.m_splitter51.Bind( wx.EVT_IDLE, self.m_splitter51OnIdle )

		self.m_panel22 = wx.Panel( self.m_splitter51, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer72 = wx.BoxSizer( wx.VERTICAL )

		self.m_splitter4 = wx.SplitterWindow( self.m_panel22, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_LIVE_UPDATE )
		self.m_splitter4.Bind( wx.EVT_IDLE, self.m_splitter4OnIdle )
		self.m_splitter4.SetMinimumPaneSize( 100 )

		self.m_panel14 = wx.Panel( self.m_splitter4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer24 = wx.BoxSizer( wx.HORIZONTAL )

		self.tree_ctrl_sessions = wx.TreeCtrl( self.m_panel14, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TR_DEFAULT_STYLE|wx.TR_FULL_ROW_HIGHLIGHT|wx.TR_HAS_BUTTONS|wx.TR_HIDE_ROOT|wx.TR_TWIST_BUTTONS )
		self.m_menu12 = wx.Menu()
		self.tree_ctrl_sessions.Bind( wx.EVT_RIGHT_DOWN, self.tree_ctrl_sessionsOnContextMenu )

		bSizer24.Add( self.tree_ctrl_sessions, 1, wx.ALL|wx.EXPAND, 5 )


		self.m_panel14.SetSizer( bSizer24 )
		self.m_panel14.Layout()
		bSizer24.Fit( self.m_panel14 )
		self.m_menu5 = wx.Menu()
		self.m_menuItem4 = wx.MenuItem( self.m_menu5, wx.ID_ANY, _(u"MyMenuItem"), wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu5.Append( self.m_menuItem4 )

		self.m_menu1 = wx.Menu()
		self.m_menuItem5 = wx.MenuItem( self.m_menu1, wx.ID_ANY, _(u"MyMenuItem"), wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu1.Append( self.m_menuItem5 )

		self.m_menu5.AppendSubMenu( self.m_menu1, _(u"MyMenu") )

		self.m_panel14.Bind( wx.EVT_RIGHT_DOWN, self.m_panel14OnContextMenu )

		self.m_panel15 = wx.Panel( self.m_splitter4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer25 = wx.BoxSizer( wx.VERTICAL )

		self.MainFrameNotebook = wx.Notebook( self.m_panel15, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.NB_FIXEDWIDTH )
		MainFrameNotebookImageSize = wx.Size( 16,16 )
		MainFrameNotebookIndex = 0
		MainFrameNotebookImages = wx.ImageList( MainFrameNotebookImageSize.GetWidth(), MainFrameNotebookImageSize.GetHeight() )
		self.MainFrameNotebook.AssignImageList( MainFrameNotebookImages )
		self.panel_system = wx.Panel( self.MainFrameNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.panel_system.Enable( False )

		bSizer272 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText291 = wx.StaticText( self.panel_system, wx.ID_ANY, _(u"MyLabel"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText291.Wrap( -1 )

		bSizer272.Add( self.m_staticText291, 0, wx.ALL, 5 )

		self.system_databases = wx.dataview.DataViewListCtrl( self.panel_system, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_dataViewListColumn1 = self.system_databases.AppendTextColumn( _(u"Databases"), wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
		self.m_dataViewListColumn2 = self.system_databases.AppendTextColumn( _(u"Size"), wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
		self.m_dataViewListColumn3 = self.system_databases.AppendTextColumn( _(u"Elements"), wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
		self.m_dataViewListColumn4 = self.system_databases.AppendTextColumn( _(u"Modified at"), wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
		self.m_dataViewListColumn5 = self.system_databases.AppendTextColumn( _(u"Tables"), wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
		bSizer272.Add( self.system_databases, 1, wx.ALL|wx.EXPAND, 5 )


		self.panel_system.SetSizer( bSizer272 )
		self.panel_system.Layout()
		bSizer272.Fit( self.panel_system )
		self.MainFrameNotebook.AddPage( self.panel_system, _(u"System"), False )
		MainFrameNotebookBitmap = wx.Bitmap( u"icons/16x16/server.png", wx.BITMAP_TYPE_ANY )
		if ( MainFrameNotebookBitmap.IsOk() ):
			MainFrameNotebookImages.Add( MainFrameNotebookBitmap )
			self.MainFrameNotebook.SetPageImage( MainFrameNotebookIndex, MainFrameNotebookIndex )
			MainFrameNotebookIndex += 1

		self.panel_database = wx.Panel( self.MainFrameNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.panel_database.Enable( False )

		bSizer27 = wx.BoxSizer( wx.VERTICAL )

		bSizer531 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText391 = wx.StaticText( self.panel_database, wx.ID_ANY, _(u"Table:"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText391.Wrap( -1 )

		bSizer531.Add( self.m_staticText391, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


		bSizer531.Add( ( 100, 0), 0, wx.EXPAND, 5 )

		self.btn_insert_table = wx.Button( self.panel_database, wx.ID_ANY, _(u"Insert"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_insert_table.SetBitmap( wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ) )
		bSizer531.Add( self.btn_insert_table, 0, wx.LEFT|wx.RIGHT, 2 )

		self.btn_delete_table = wx.Button( self.panel_database, wx.ID_ANY, _(u"Delete"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_delete_table.SetBitmap( wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ) )
		self.btn_delete_table.Enable( False )

		bSizer531.Add( self.btn_delete_table, 0, wx.LEFT|wx.RIGHT, 2 )


		bSizer531.Add( ( 0, 0), 1, wx.EXPAND, 5 )


		bSizer27.Add( bSizer531, 0, wx.EXPAND, 5 )

		self.m_dataViewListCtrl2 = wx.dataview.DataViewListCtrl( self.panel_database, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_dataViewListColumn6 = self.m_dataViewListCtrl2.AppendTextColumn( _(u"Name"), wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
		self.m_dataViewListColumn7 = self.m_dataViewListCtrl2.AppendTextColumn( _(u"Lines"), wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
		self.m_dataViewListColumn8 = self.m_dataViewListCtrl2.AppendTextColumn( _(u"Size"), wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
		self.m_dataViewListColumn9 = self.m_dataViewListCtrl2.AppendTextColumn( _(u"Created at"), wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
		self.m_dataViewListColumn10 = self.m_dataViewListCtrl2.AppendTextColumn( _(u"Updated at"), wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
		self.m_dataViewListColumn11 = self.m_dataViewListCtrl2.AppendTextColumn( _(u"Engine"), wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
		self.m_dataViewListColumn12 = self.m_dataViewListCtrl2.AppendTextColumn( _(u"Comments"), wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
		bSizer27.Add( self.m_dataViewListCtrl2, 1, wx.ALL|wx.EXPAND, 5 )


		self.panel_database.SetSizer( bSizer27 )
		self.panel_database.Layout()
		bSizer27.Fit( self.panel_database )
		self.m_menu15 = wx.Menu()
		self.panel_database.Bind( wx.EVT_RIGHT_DOWN, self.panel_databaseOnContextMenu )

		self.MainFrameNotebook.AddPage( self.panel_database, _(u"Database"), False )
		MainFrameNotebookBitmap = wx.Bitmap( u"icons/16x16/database.png", wx.BITMAP_TYPE_ANY )
		if ( MainFrameNotebookBitmap.IsOk() ):
			MainFrameNotebookImages.Add( MainFrameNotebookBitmap )
			self.MainFrameNotebook.SetPageImage( MainFrameNotebookIndex, MainFrameNotebookIndex )
			MainFrameNotebookIndex += 1

		self.panel_table = wx.Panel( self.MainFrameNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.panel_table.Enable( False )

		bSizer251 = wx.BoxSizer( wx.VERTICAL )

		self.m_splitter41 = wx.SplitterWindow( self.panel_table, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_LIVE_UPDATE )
		self.m_splitter41.Bind( wx.EVT_IDLE, self.m_splitter41OnIdle )
		self.m_splitter41.SetMinimumPaneSize( 200 )

		self.m_panel19 = wx.Panel( self.m_splitter41, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer55 = wx.BoxSizer( wx.VERTICAL )

		self.m_notebook3 = wx.Notebook( self.m_panel19, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.NB_FIXEDWIDTH )
		m_notebook3ImageSize = wx.Size( 16,16 )
		m_notebook3Index = 0
		m_notebook3Images = wx.ImageList( m_notebook3ImageSize.GetWidth(), m_notebook3ImageSize.GetHeight() )
		self.m_notebook3.AssignImageList( m_notebook3Images )
		self.PanelTableBase = wx.Panel( self.m_notebook3, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer262 = wx.BoxSizer( wx.VERTICAL )

		bSizer271 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText8 = wx.StaticText( self.PanelTableBase, wx.ID_ANY, _(u"Name"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText8.Wrap( -1 )

		bSizer271.Add( self.m_staticText8, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.table_name = wx.TextCtrl( self.PanelTableBase, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer271.Add( self.table_name, 1, wx.ALL|wx.EXPAND, 5 )


		bSizer262.Add( bSizer271, 0, wx.EXPAND, 5 )

		bSizer273 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText83 = wx.StaticText( self.PanelTableBase, wx.ID_ANY, _(u"Comments"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText83.Wrap( -1 )

		bSizer273.Add( self.m_staticText83, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.table_comment = wx.TextCtrl( self.PanelTableBase, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE )
		bSizer273.Add( self.table_comment, 1, wx.ALL|wx.EXPAND, 5 )


		bSizer262.Add( bSizer273, 1, wx.EXPAND, 5 )


		self.PanelTableBase.SetSizer( bSizer262 )
		self.PanelTableBase.Layout()
		bSizer262.Fit( self.PanelTableBase )
		self.m_notebook3.AddPage( self.PanelTableBase, _(u"Base"), True )
		m_notebook3Bitmap = wx.Bitmap( u"icons/16x16/table.png", wx.BITMAP_TYPE_ANY )
		if ( m_notebook3Bitmap.IsOk() ):
			m_notebook3Images.Add( m_notebook3Bitmap )
			self.m_notebook3.SetPageImage( m_notebook3Index, m_notebook3Index )
			m_notebook3Index += 1

		self.PanelTableOptions = wx.Panel( self.m_notebook3, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer261 = wx.BoxSizer( wx.VERTICAL )

		gSizer11 = wx.GridSizer( 0, 2, 0, 0 )

		bSizer27111 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText8111 = wx.StaticText( self.PanelTableOptions, wx.ID_ANY, _(u"Auto Increment"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText8111.Wrap( -1 )

		bSizer27111.Add( self.m_staticText8111, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.table_auto_increment = wx.TextCtrl( self.PanelTableOptions, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer27111.Add( self.table_auto_increment, 1, wx.ALL|wx.EXPAND, 5 )


		gSizer11.Add( bSizer27111, 1, wx.EXPAND, 5 )

		bSizer2712 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText812 = wx.StaticText( self.PanelTableOptions, wx.ID_ANY, _(u"Engine"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText812.Wrap( -1 )

		bSizer2712.Add( self.m_staticText812, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		table_engineChoices = [ wx.EmptyString ]
		self.table_engine = wx.Choice( self.PanelTableOptions, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, table_engineChoices, 0 )
		self.table_engine.SetSelection( 1 )
		bSizer2712.Add( self.table_engine, 1, wx.ALL|wx.EXPAND, 5 )


		gSizer11.Add( bSizer2712, 0, wx.EXPAND, 5 )

		bSizer2721 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText821 = wx.StaticText( self.PanelTableOptions, wx.ID_ANY, _(u"Default Collation"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText821.Wrap( -1 )

		bSizer2721.Add( self.m_staticText821, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.table_collation = wx.TextCtrl( self.PanelTableOptions, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2721.Add( self.table_collation, 1, wx.ALL|wx.EXPAND, 5 )


		gSizer11.Add( bSizer2721, 0, wx.EXPAND, 5 )


		bSizer261.Add( gSizer11, 0, wx.EXPAND, 5 )


		self.PanelTableOptions.SetSizer( bSizer261 )
		self.PanelTableOptions.Layout()
		bSizer261.Fit( self.PanelTableOptions )
		self.m_notebook3.AddPage( self.PanelTableOptions, _(u"Options"), False )
		m_notebook3Bitmap = wx.Bitmap( u"icons/16x16/wrench.png", wx.BITMAP_TYPE_ANY )
		if ( m_notebook3Bitmap.IsOk() ):
			m_notebook3Images.Add( m_notebook3Bitmap )
			self.m_notebook3.SetPageImage( m_notebook3Index, m_notebook3Index )
			m_notebook3Index += 1

		self.PanelTableIndex = wx.Panel( self.m_notebook3, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer28 = wx.BoxSizer( wx.HORIZONTAL )

		bSizer791 = wx.BoxSizer( wx.VERTICAL )

		self.btn_index_insert = wx.Button( self.PanelTableIndex, wx.ID_ANY, _(u"Insert"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_index_insert.SetBitmap( wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ) )
		self.btn_index_insert.Hide()

		bSizer791.Add( self.btn_index_insert, 0, wx.ALL|wx.EXPAND, 5 )

		self.btn_index_delete = wx.Button( self.PanelTableIndex, wx.ID_ANY, _(u"Remove"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_index_delete.SetBitmap( wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ) )
		self.btn_index_delete.Enable( False )

		bSizer791.Add( self.btn_index_delete, 0, wx.ALL|wx.EXPAND, 5 )

		self.btn_index_clear = wx.Button( self.PanelTableIndex, wx.ID_ANY, _(u"Clear"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_index_clear.SetBitmap( wx.Bitmap( u"icons/16x16/cross.png", wx.BITMAP_TYPE_ANY ) )
		bSizer791.Add( self.btn_index_clear, 0, wx.ALL|wx.EXPAND, 5 )


		bSizer28.Add( bSizer791, 0, wx.ALIGN_CENTER, 5 )

		self.dv_table_indexes = TableIndexesDataViewCtrl( self.PanelTableIndex, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer28.Add( self.dv_table_indexes, 1, wx.ALL|wx.EXPAND, 0 )


		self.PanelTableIndex.SetSizer( bSizer28 )
		self.PanelTableIndex.Layout()
		bSizer28.Fit( self.PanelTableIndex )
		self.m_notebook3.AddPage( self.PanelTableIndex, _(u"Indexes"), False )
		m_notebook3Bitmap = wx.Bitmap( u"icons/16x16/lightning.png", wx.BITMAP_TYPE_ANY )
		if ( m_notebook3Bitmap.IsOk() ):
			m_notebook3Images.Add( m_notebook3Bitmap )
			self.m_notebook3.SetPageImage( m_notebook3Index, m_notebook3Index )
			m_notebook3Index += 1

		self.PanelTableFK = wx.Panel( self.m_notebook3, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer77 = wx.BoxSizer( wx.VERTICAL )

		bSizer78 = wx.BoxSizer( wx.HORIZONTAL )

		bSizer79 = wx.BoxSizer( wx.VERTICAL )

		self.btn_foreign_key_insert = wx.Button( self.PanelTableFK, wx.ID_ANY, _(u"Insert"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_foreign_key_insert.SetBitmap( wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ) )
		bSizer79.Add( self.btn_foreign_key_insert, 0, wx.ALL|wx.EXPAND, 5 )

		self.btn_foreign_key_delete = wx.Button( self.PanelTableFK, wx.ID_ANY, _(u"Remove"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_foreign_key_delete.SetBitmap( wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ) )
		self.btn_foreign_key_delete.Enable( False )

		bSizer79.Add( self.btn_foreign_key_delete, 0, wx.ALL|wx.EXPAND, 5 )

		self.btn_foreign_key_clear = wx.Button( self.PanelTableFK, wx.ID_ANY, _(u"Clear"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_foreign_key_clear.SetBitmap( wx.Bitmap( u"icons/16x16/cross.png", wx.BITMAP_TYPE_ANY ) )
		bSizer79.Add( self.btn_foreign_key_clear, 0, wx.ALL|wx.EXPAND, 5 )


		bSizer78.Add( bSizer79, 0, wx.ALIGN_CENTER, 5 )

		self.dv_table_foreign_keys = TableForeignKeysDataViewCtrl( self.PanelTableFK, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer78.Add( self.dv_table_foreign_keys, 1, wx.ALL|wx.EXPAND, 0 )


		bSizer77.Add( bSizer78, 1, wx.EXPAND, 5 )


		self.PanelTableFK.SetSizer( bSizer77 )
		self.PanelTableFK.Layout()
		bSizer77.Fit( self.PanelTableFK )
		self.m_notebook3.AddPage( self.PanelTableFK, _(u"Foreign Key"), False )
		m_notebook3Bitmap = wx.Bitmap( u"icons/16x16/table_relationship.png", wx.BITMAP_TYPE_ANY )
		if ( m_notebook3Bitmap.IsOk() ):
			m_notebook3Images.Add( m_notebook3Bitmap )
			self.m_notebook3.SetPageImage( m_notebook3Index, m_notebook3Index )
			m_notebook3Index += 1


		bSizer55.Add( self.m_notebook3, 1, wx.EXPAND | wx.ALL, 5 )


		self.m_panel19.SetSizer( bSizer55 )
		self.m_panel19.Layout()
		bSizer55.Fit( self.m_panel19 )
		self.panel_table_columns = wx.Panel( self.m_splitter41, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.panel_table_columns.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

		bSizer54 = wx.BoxSizer( wx.VERTICAL )

		bSizer53 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText39 = wx.StaticText( self.panel_table_columns, wx.ID_ANY, _(u"Columns:"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText39.Wrap( -1 )

		bSizer53.Add( self.m_staticText39, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


		bSizer53.Add( ( 100, 0), 0, wx.EXPAND, 5 )

		self.btn_insert_column = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Insert"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_insert_column.SetBitmap( wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ) )
		bSizer53.Add( self.btn_insert_column, 0, wx.LEFT|wx.RIGHT, 2 )

		self.btn_column_delete = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Delete"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_column_delete.SetBitmap( wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ) )
		self.btn_column_delete.Enable( False )

		bSizer53.Add( self.btn_column_delete, 0, wx.LEFT|wx.RIGHT, 2 )

		self.btn_column_move_up = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Up"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_column_move_up.SetBitmap( wx.Bitmap( u"icons/16x16/arrow_up.png", wx.BITMAP_TYPE_ANY ) )
		self.btn_column_move_up.Enable( False )

		bSizer53.Add( self.btn_column_move_up, 0, wx.LEFT|wx.RIGHT, 2 )

		self.btn_column_move_down = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Down"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_column_move_down.SetBitmap( wx.Bitmap( u"icons/16x16/arrow_down.png", wx.BITMAP_TYPE_ANY ) )
		self.btn_column_move_down.Enable( False )

		bSizer53.Add( self.btn_column_move_down, 0, wx.LEFT|wx.RIGHT, 2 )


		bSizer53.Add( ( 0, 0), 1, wx.EXPAND, 5 )


		bSizer54.Add( bSizer53, 0, wx.ALL|wx.EXPAND, 5 )

		self.list_ctrl_table_columns = TableColumnsDataViewCtrl( self.panel_table_columns, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer54.Add( self.list_ctrl_table_columns, 1, wx.ALL|wx.EXPAND, 5 )

		bSizer52 = wx.BoxSizer( wx.HORIZONTAL )

		self.btn_table_delete = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Delete"), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer52.Add( self.btn_table_delete, 0, wx.ALL, 5 )

		self.btn_table_cancel = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Cancel"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.btn_table_cancel.Enable( False )

		bSizer52.Add( self.btn_table_cancel, 0, wx.ALL, 5 )

		self.btn_table_save = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Save"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.btn_table_save.Enable( False )

		bSizer52.Add( self.btn_table_save, 0, wx.ALL, 5 )


		bSizer54.Add( bSizer52, 0, wx.EXPAND, 5 )


		self.panel_table_columns.SetSizer( bSizer54 )
		self.panel_table_columns.Layout()
		bSizer54.Fit( self.panel_table_columns )
		self.menu_table_columns = wx.Menu()
		self.add_index = wx.MenuItem( self.menu_table_columns, wx.ID_ANY, _(u"Add Index"), wx.EmptyString, wx.ITEM_NORMAL )
		self.menu_table_columns.Append( self.add_index )

		self.m_menu21 = wx.Menu()
		self.m_menuItem8 = wx.MenuItem( self.m_menu21, wx.ID_ANY, _(u"Add PrimaryKey"), wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu21.Append( self.m_menuItem8 )

		self.m_menuItem9 = wx.MenuItem( self.m_menu21, wx.ID_ANY, _(u"Add Index"), wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu21.Append( self.m_menuItem9 )

		self.menu_table_columns.AppendSubMenu( self.m_menu21, _(u"MyMenu") )

		self.panel_table_columns.Bind( wx.EVT_RIGHT_DOWN, self.panel_table_columnsOnContextMenu )

		self.m_splitter41.SplitHorizontally( self.m_panel19, self.panel_table_columns, 200 )
		bSizer251.Add( self.m_splitter41, 1, wx.EXPAND, 0 )


		self.panel_table.SetSizer( bSizer251 )
		self.panel_table.Layout()
		bSizer251.Fit( self.panel_table )
		self.MainFrameNotebook.AddPage( self.panel_table, _(u"Table"), True )
		MainFrameNotebookBitmap = wx.Bitmap( u"icons/16x16/table.png", wx.BITMAP_TYPE_ANY )
		if ( MainFrameNotebookBitmap.IsOk() ):
			MainFrameNotebookImages.Add( MainFrameNotebookBitmap )
			self.MainFrameNotebook.SetPageImage( MainFrameNotebookIndex, MainFrameNotebookIndex )
			MainFrameNotebookIndex += 1

		self.panel_records = wx.Panel( self.MainFrameNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.panel_records.Enable( False )

		bSizer61 = wx.BoxSizer( wx.VERTICAL )

		self.list_ctrl_table_records = TableRecordsDataViewCtrl( self.panel_records, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer61.Add( self.list_ctrl_table_records, 1, wx.ALL|wx.EXPAND, 5 )


		self.panel_records.SetSizer( bSizer61 )
		self.panel_records.Layout()
		bSizer61.Fit( self.panel_records )
		self.MainFrameNotebook.AddPage( self.panel_records, _(u"Data"), False )
		MainFrameNotebookBitmap = wx.Bitmap( u"icons/16x16/text_columns.png", wx.BITMAP_TYPE_ANY )
		if ( MainFrameNotebookBitmap.IsOk() ):
			MainFrameNotebookImages.Add( MainFrameNotebookBitmap )
			self.MainFrameNotebook.SetPageImage( MainFrameNotebookIndex, MainFrameNotebookIndex )
			MainFrameNotebookIndex += 1

		self.QueryPanel = wx.Panel( self.MainFrameNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.QueryPanel.Enable( False )

		bSizer26 = wx.BoxSizer( wx.VERTICAL )

		self.m_textCtrl10 = wx.TextCtrl( self.QueryPanel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE|wx.TE_RICH|wx.TE_RICH2 )
		bSizer26.Add( self.m_textCtrl10, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_button12 = wx.Button( self.QueryPanel, wx.ID_ANY, _(u"New"), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer26.Add( self.m_button12, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )


		self.QueryPanel.SetSizer( bSizer26 )
		self.QueryPanel.Layout()
		bSizer26.Fit( self.QueryPanel )
		self.MainFrameNotebook.AddPage( self.QueryPanel, _(u"Query"), False )
		MainFrameNotebookBitmap = wx.Bitmap( u"icons/16x16/arrow_right.png", wx.BITMAP_TYPE_ANY )
		if ( MainFrameNotebookBitmap.IsOk() ):
			MainFrameNotebookImages.Add( MainFrameNotebookBitmap )
			self.MainFrameNotebook.SetPageImage( MainFrameNotebookIndex, MainFrameNotebookIndex )
			MainFrameNotebookIndex += 1

		self.QueryPanelTpl = wx.Panel( self.MainFrameNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.QueryPanelTpl.Hide()

		bSizer263 = wx.BoxSizer( wx.VERTICAL )

		self.m_textCtrl101 = wx.TextCtrl( self.QueryPanelTpl, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE|wx.TE_RICH|wx.TE_RICH2 )
		bSizer263.Add( self.m_textCtrl101, 1, wx.ALL|wx.EXPAND, 5 )

		bSizer49 = wx.BoxSizer( wx.HORIZONTAL )


		bSizer49.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_button17 = wx.Button( self.QueryPanelTpl, wx.ID_ANY, _(u"Close"), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer49.Add( self.m_button17, 0, wx.ALL, 5 )

		self.m_button121 = wx.Button( self.QueryPanelTpl, wx.ID_ANY, _(u"New"), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer49.Add( self.m_button121, 0, wx.ALL, 5 )


		bSizer263.Add( bSizer49, 0, wx.EXPAND, 5 )


		self.QueryPanelTpl.SetSizer( bSizer263 )
		self.QueryPanelTpl.Layout()
		bSizer263.Fit( self.QueryPanelTpl )
		self.MainFrameNotebook.AddPage( self.QueryPanelTpl, _(u"Query #2"), False )

		bSizer25.Add( self.MainFrameNotebook, 1, wx.ALL|wx.EXPAND, 5 )


		self.m_panel15.SetSizer( bSizer25 )
		self.m_panel15.Layout()
		bSizer25.Fit( self.m_panel15 )
		self.m_menu3 = wx.Menu()
		self.m_menuItem3 = wx.MenuItem( self.m_menu3, wx.ID_ANY, _(u"MyMenuItem"), wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu3.Append( self.m_menuItem3 )

		self.m_panel15.Bind( wx.EVT_RIGHT_DOWN, self.m_panel15OnContextMenu )

		self.m_splitter4.SplitVertically( self.m_panel14, self.m_panel15, 300 )
		bSizer72.Add( self.m_splitter4, 1, wx.EXPAND, 5 )


		self.m_panel22.SetSizer( bSizer72 )
		self.m_panel22.Layout()
		bSizer72.Fit( self.m_panel22 )
		self.LogSQLPanel = wx.Panel( self.m_splitter51, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,-1 ), wx.TAB_TRAVERSAL )
		sizer_log_sql = wx.BoxSizer( wx.VERTICAL )

		self.query_logs = wx.stc.StyledTextCtrl( self.LogSQLPanel, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,200 ), 0)
		self.query_logs.SetUseTabs ( True )
		self.query_logs.SetTabWidth ( 4 )
		self.query_logs.SetIndent ( 4 )
		self.query_logs.SetTabIndents( True )
		self.query_logs.SetBackSpaceUnIndents( True )
		self.query_logs.SetViewEOL( False )
		self.query_logs.SetViewWhiteSpace( False )
		self.query_logs.SetMarginWidth( 2, 0 )
		self.query_logs.SetIndentationGuides( True )
		self.query_logs.SetReadOnly( False )
		self.query_logs.SetMarginWidth( 1, 0 )
		self.query_logs.SetMarginType( 0, wx.stc.STC_MARGIN_NUMBER )
		self.query_logs.SetMarginWidth( 0, self.query_logs.TextWidth( wx.stc.STC_STYLE_LINENUMBER, "_99999" ) )
		self.query_logs.MarkerDefine( wx.stc.STC_MARKNUM_FOLDER, wx.stc.STC_MARK_BOXPLUS )
		self.query_logs.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDER, wx.BLACK)
		self.query_logs.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDER, wx.WHITE)
		self.query_logs.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.stc.STC_MARK_BOXMINUS )
		self.query_logs.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.BLACK )
		self.query_logs.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.WHITE )
		self.query_logs.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERSUB, wx.stc.STC_MARK_EMPTY )
		self.query_logs.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEREND, wx.stc.STC_MARK_BOXPLUS )
		self.query_logs.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEREND, wx.BLACK )
		self.query_logs.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEREND, wx.WHITE )
		self.query_logs.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.stc.STC_MARK_BOXMINUS )
		self.query_logs.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.BLACK)
		self.query_logs.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.WHITE)
		self.query_logs.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERMIDTAIL, wx.stc.STC_MARK_EMPTY )
		self.query_logs.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERTAIL, wx.stc.STC_MARK_EMPTY )
		self.query_logs.SetSelBackground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT ) )
		self.query_logs.SetSelForeground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT ) )
		sizer_log_sql.Add( self.query_logs, 1, wx.EXPAND | wx.ALL, 5 )


		self.LogSQLPanel.SetSizer( sizer_log_sql )
		self.LogSQLPanel.Layout()
		sizer_log_sql.Fit( self.LogSQLPanel )
		self.m_splitter51.SplitHorizontally( self.m_panel22, self.LogSQLPanel, -150 )
		bSizer21.Add( self.m_splitter51, 1, wx.EXPAND, 5 )


		self.m_panel13.SetSizer( bSizer21 )
		self.m_panel13.Layout()
		bSizer21.Fit( self.m_panel13 )
		bSizer19.Add( self.m_panel13, 1, wx.EXPAND | wx.ALL, 0 )


		self.SetSizer( bSizer19 )
		self.Layout()
		self.status_bar = self.CreateStatusBar( 4, wx.STB_SIZEGRIP, wx.ID_ANY )

		self.Centre( wx.BOTH )

		# Connect Events
		self.Bind( wx.EVT_CLOSE, self.do_close )
		self.Bind( wx.EVT_TOOL, self.do_open_session_manager, id = self.m_tool5.GetId() )
		self.Bind( wx.EVT_TOOL, self.do_disconnect, id = self.m_tool4.GetId() )
		self.tree_ctrl_sessions.Bind( wx.EVT_TREE_ITEM_RIGHT_CLICK, self.show_tree_ctrl_menu )
		self.MainFrameNotebook.Bind( wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_chaged )
		self.btn_insert_table.Bind( wx.EVT_BUTTON, self.on_insert_table )
		self.btn_index_insert.Bind( wx.EVT_BUTTON, self.on_foreign_key_insert )
		self.btn_index_delete.Bind( wx.EVT_BUTTON, self.on_index_delete )
		self.btn_index_clear.Bind( wx.EVT_BUTTON, self.on_index_clear )
		self.btn_foreign_key_insert.Bind( wx.EVT_BUTTON, self.on_foreign_key_insert )
		self.btn_foreign_key_delete.Bind( wx.EVT_BUTTON, self.on_foreign_key_delete )
		self.btn_foreign_key_clear.Bind( wx.EVT_BUTTON, self.on_foreign_key_clear )
		self.btn_insert_column.Bind( wx.EVT_BUTTON, self.on_column_insert )
		self.btn_column_delete.Bind( wx.EVT_BUTTON, self.on_column_delete )
		self.btn_column_move_up.Bind( wx.EVT_BUTTON, self.on_column_move_up )
		self.btn_column_move_down.Bind( wx.EVT_BUTTON, self.on_column_move_down )
		self.btn_table_delete.Bind( wx.EVT_BUTTON, self.on_delete_table )
		self.btn_table_cancel.Bind( wx.EVT_BUTTON, self.do_cancel_table )
		self.btn_table_save.Bind( wx.EVT_BUTTON, self.do_save_table )

	def __del__( self ):
		pass


	# Virtual event handlers, override them in your derived class
	def do_close( self, event ):
		event.Skip()

	def do_open_session_manager( self, event ):
		event.Skip()

	def do_disconnect( self, event ):
		event.Skip()

	def show_tree_ctrl_menu( self, event ):
		event.Skip()

	def on_page_chaged( self, event ):
		event.Skip()

	def on_insert_table( self, event ):
		event.Skip()

	def on_foreign_key_insert( self, event ):
		event.Skip()

	def on_index_delete( self, event ):
		event.Skip()

	def on_index_clear( self, event ):
		event.Skip()


	def on_foreign_key_delete( self, event ):
		event.Skip()

	def on_foreign_key_clear( self, event ):
		event.Skip()

	def on_column_insert( self, event ):
		event.Skip()

	def on_column_delete( self, event ):
		event.Skip()

	def on_column_move_up( self, event ):
		event.Skip()

	def on_column_move_down( self, event ):
		event.Skip()

	def on_delete_table( self, event ):
		event.Skip()

	def do_cancel_table( self, event ):
		event.Skip()

	def do_save_table( self, event ):
		event.Skip()

	def m_splitter51OnIdle( self, event ):
		self.m_splitter51.SetSashPosition( -150 )
		self.m_splitter51.Unbind( wx.EVT_IDLE )

	def m_splitter4OnIdle( self, event ):
		self.m_splitter4.SetSashPosition( 300 )
		self.m_splitter4.Unbind( wx.EVT_IDLE )

	def tree_ctrl_sessionsOnContextMenu( self, event ):
		self.tree_ctrl_sessions.PopupMenu( self.m_menu12, event.GetPosition() )

	def m_panel14OnContextMenu( self, event ):
		self.m_panel14.PopupMenu( self.m_menu5, event.GetPosition() )

	def panel_databaseOnContextMenu( self, event ):
		self.panel_database.PopupMenu( self.m_menu15, event.GetPosition() )

	def m_splitter41OnIdle( self, event ):
		self.m_splitter41.SetSashPosition( 200 )
		self.m_splitter41.Unbind( wx.EVT_IDLE )

	def panel_table_columnsOnContextMenu( self, event ):
		self.panel_table_columns.PopupMenu( self.menu_table_columns, event.GetPosition() )

	def m_panel15OnContextMenu( self, event ):
		self.m_panel15.PopupMenu( self.m_menu3, event.GetPosition() )


###########################################################################
## Class EditColumnView
###########################################################################

class EditColumnView ( wx.Dialog ):

	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = _(u"Edit Column"), pos = wx.DefaultPosition, size = wx.Size( 600,600 ), style = wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		bSizer98 = wx.BoxSizer( wx.VERTICAL )

		bSizer52 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText26 = wx.StaticText( self, wx.ID_ANY, _(u"Name"), wx.DefaultPosition, wx.Size( 100,-1 ), wx.ST_NO_AUTORESIZE )
		self.m_staticText26.Wrap( -1 )

		bSizer52.Add( self.m_staticText26, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

		self.column_name = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer52.Add( self.column_name, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

		self.m_staticText261 = wx.StaticText( self, wx.ID_ANY, _(u"Datatype"), wx.DefaultPosition, wx.Size( 100,-1 ), 0 )
		self.m_staticText261.Wrap( -1 )

		bSizer52.Add( self.m_staticText261, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

		column_datatypeChoices = []
		self.column_datatype = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, column_datatypeChoices, 0 )
		self.column_datatype.SetSelection( 0 )
		bSizer52.Add( self.column_datatype, 1, wx.ALL, 5 )


		bSizer98.Add( bSizer52, 0, wx.EXPAND, 5 )

		bSizer5211 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText2611 = wx.StaticText( self, wx.ID_ANY, _(u"Length/Set"), wx.DefaultPosition, wx.Size( 100,-1 ), 0 )
		self.m_staticText2611.Wrap( -1 )

		bSizer5211.Add( self.m_staticText2611, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

		bSizer60 = wx.BoxSizer( wx.HORIZONTAL )

		self.column_set = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer60.Add( self.column_set, 1, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.column_length = wx.SpinCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 65536, 0 )
		bSizer60.Add( self.column_length, 1, wx.ALL, 5 )

		self.column_scale = wx.SpinCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_WRAP, 0, 65536, 0 )
		self.column_scale.Enable( False )

		bSizer60.Add( self.column_scale, 1, wx.ALL, 5 )


		bSizer5211.Add( bSizer60, 1, wx.EXPAND, 5 )

		self.m_staticText261111112 = wx.StaticText( self, wx.ID_ANY, _(u"Collation"), wx.DefaultPosition, wx.Size( 100,-1 ), 0 )
		self.m_staticText261111112.Wrap( -1 )

		bSizer5211.Add( self.m_staticText261111112, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

		column_collationChoices = []
		self.column_collation = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, column_collationChoices, 0 )
		self.column_collation.SetSelection( 0 )
		bSizer5211.Add( self.column_collation, 1, wx.ALL, 5 )


		bSizer98.Add( bSizer5211, 0, wx.EXPAND, 5 )

		bSizer52111 = wx.BoxSizer( wx.HORIZONTAL )


		bSizer52111.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.column_unsigned = wx.CheckBox( self, wx.ID_ANY, _(u"Unsigned"), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer52111.Add( self.column_unsigned, 1, wx.ALL, 5 )


		bSizer52111.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.column_allow_null = wx.CheckBox( self, wx.ID_ANY, _(u"Allow NULL"), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer52111.Add( self.column_allow_null, 1, wx.ALL, 5 )


		bSizer52111.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.column_zero_fill = wx.CheckBox( self, wx.ID_ANY, _(u"Zero Fill"), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer52111.Add( self.column_zero_fill, 1, wx.ALL, 5 )


		bSizer52111.Add( ( 0, 0), 1, wx.EXPAND, 5 )


		bSizer98.Add( bSizer52111, 0, wx.EXPAND, 5 )

		bSizer53 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText26111111 = wx.StaticText( self, wx.ID_ANY, _(u"Default"), wx.DefaultPosition, wx.Size( 100,-1 ), 0 )
		self.m_staticText26111111.Wrap( -1 )

		bSizer53.Add( self.m_staticText26111111, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

		self.column_default = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer53.Add( self.column_default, 1, wx.ALL, 5 )


		bSizer98.Add( bSizer53, 0, wx.EXPAND, 5 )

		bSizer531 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText261111111 = wx.StaticText( self, wx.ID_ANY, _(u"Comments"), wx.DefaultPosition, wx.Size( 100,-1 ), 0 )
		self.m_staticText261111111.Wrap( -1 )

		bSizer531.Add( self.m_staticText261111111, 0, wx.ALL, 5 )

		self.column_comments = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,100 ), wx.TE_MULTILINE )
		bSizer531.Add( self.column_comments, 1, wx.ALL, 5 )


		bSizer98.Add( bSizer531, 0, wx.EXPAND, 5 )

		bSizer532 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText261111113 = wx.StaticText( self, wx.ID_ANY, _(u"Virtuality"), wx.DefaultPosition, wx.Size( 100,-1 ), 0 )
		self.m_staticText261111113.Wrap( -1 )

		bSizer532.Add( self.m_staticText261111113, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

		column_virtualityChoices = []
		self.column_virtuality = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, column_virtualityChoices, 0 )
		self.column_virtuality.SetSelection( 0 )
		bSizer532.Add( self.column_virtuality, 1, wx.ALL, 5 )


		bSizer98.Add( bSizer532, 0, wx.EXPAND, 5 )

		bSizer5311 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText2611111111 = wx.StaticText( self, wx.ID_ANY, _(u"Expression"), wx.DefaultPosition, wx.Size( 100,-1 ), 0 )
		self.m_staticText2611111111.Wrap( -1 )

		bSizer5311.Add( self.m_staticText2611111111, 0, wx.ALL, 5 )

		self.column_expression = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,100 ), wx.TE_MULTILINE )
		bSizer5311.Add( self.column_expression, 1, wx.ALL, 5 )


		bSizer98.Add( bSizer5311, 0, wx.EXPAND, 5 )


		bSizer98.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_staticline2 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer98.Add( self.m_staticline2, 0, wx.EXPAND | wx.ALL, 5 )

		bSizer64 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_button16 = wx.Button( self, wx.ID_ANY, _(u"Cancel"), wx.DefaultPosition, wx.DefaultSize, 0 )

		self.m_button16.SetDefault()

		self.m_button16.SetBitmap( wx.Bitmap( u"icons/16x16/cancel.png", wx.BITMAP_TYPE_ANY ) )
		bSizer64.Add( self.m_button16, 0, wx.ALL, 5 )


		bSizer64.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_button15 = wx.Button( self, wx.ID_ANY, _(u"Save"), wx.DefaultPosition, wx.DefaultSize, 0 )

		self.m_button15.SetBitmap( wx.Bitmap( u"icons/16x16/disk.png", wx.BITMAP_TYPE_ANY ) )
		bSizer64.Add( self.m_button15, 0, wx.ALL, 5 )


		bSizer98.Add( bSizer64, 0, wx.EXPAND, 5 )


		self.SetSizer( bSizer98 )
		self.Layout()

		self.Centre( wx.BOTH )

	def __del__( self ):
		pass


###########################################################################
## Class MyPanel1
###########################################################################

class MyPanel1 ( wx.Panel ):

	def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
		wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )


	def __del__( self ):
		pass


###########################################################################
## Class TablePanel
###########################################################################

class TablePanel ( wx.Panel ):

	def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 640,480 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
		wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

		bSizer251 = wx.BoxSizer( wx.VERTICAL )

		self.m_splitter41 = wx.SplitterWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_LIVE_UPDATE )
		self.m_splitter41.Bind( wx.EVT_IDLE, self.m_splitter41OnIdle )
		self.m_splitter41.SetMinimumPaneSize( 200 )

		self.m_panel19 = wx.Panel( self.m_splitter41, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer55 = wx.BoxSizer( wx.VERTICAL )

		self.m_notebook3 = wx.Notebook( self.m_panel19, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.NB_FIXEDWIDTH )
		m_notebook3ImageSize = wx.Size( 16,16 )
		m_notebook3Index = 0
		m_notebook3Images = wx.ImageList( m_notebook3ImageSize.GetWidth(), m_notebook3ImageSize.GetHeight() )
		self.m_notebook3.AssignImageList( m_notebook3Images )
		self.PanelTableBase = wx.Panel( self.m_notebook3, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer262 = wx.BoxSizer( wx.VERTICAL )

		bSizer271 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText8 = wx.StaticText( self.PanelTableBase, wx.ID_ANY, _(u"Name"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText8.Wrap( -1 )

		bSizer271.Add( self.m_staticText8, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.table_name = wx.TextCtrl( self.PanelTableBase, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer271.Add( self.table_name, 1, wx.ALL|wx.EXPAND, 5 )


		bSizer262.Add( bSizer271, 0, wx.EXPAND, 5 )

		bSizer273 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText83 = wx.StaticText( self.PanelTableBase, wx.ID_ANY, _(u"Comments"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText83.Wrap( -1 )

		bSizer273.Add( self.m_staticText83, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.table_comment = wx.TextCtrl( self.PanelTableBase, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE )
		bSizer273.Add( self.table_comment, 1, wx.ALL|wx.EXPAND, 5 )


		bSizer262.Add( bSizer273, 1, wx.EXPAND, 5 )


		self.PanelTableBase.SetSizer( bSizer262 )
		self.PanelTableBase.Layout()
		bSizer262.Fit( self.PanelTableBase )
		self.m_notebook3.AddPage( self.PanelTableBase, _(u"Base"), True )
		m_notebook3Bitmap = wx.Bitmap( u"icons/16x16/table.png", wx.BITMAP_TYPE_ANY )
		if ( m_notebook3Bitmap.IsOk() ):
			m_notebook3Images.Add( m_notebook3Bitmap )
			self.m_notebook3.SetPageImage( m_notebook3Index, m_notebook3Index )
			m_notebook3Index += 1

		self.PanelTableOptions = wx.Panel( self.m_notebook3, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer261 = wx.BoxSizer( wx.VERTICAL )

		gSizer11 = wx.GridSizer( 0, 2, 0, 0 )

		bSizer27111 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText8111 = wx.StaticText( self.PanelTableOptions, wx.ID_ANY, _(u"Auto Increment"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText8111.Wrap( -1 )

		bSizer27111.Add( self.m_staticText8111, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.table_auto_increment = wx.TextCtrl( self.PanelTableOptions, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer27111.Add( self.table_auto_increment, 1, wx.ALL|wx.EXPAND, 5 )


		gSizer11.Add( bSizer27111, 1, wx.EXPAND, 5 )

		bSizer2712 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText812 = wx.StaticText( self.PanelTableOptions, wx.ID_ANY, _(u"Engine"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText812.Wrap( -1 )

		bSizer2712.Add( self.m_staticText812, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		table_engineChoices = [ wx.EmptyString ]
		self.table_engine = wx.Choice( self.PanelTableOptions, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, table_engineChoices, 0 )
		self.table_engine.SetSelection( 1 )
		bSizer2712.Add( self.table_engine, 1, wx.ALL|wx.EXPAND, 5 )


		gSizer11.Add( bSizer2712, 0, wx.EXPAND, 5 )

		bSizer2721 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText821 = wx.StaticText( self.PanelTableOptions, wx.ID_ANY, _(u"Default Collation"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
		self.m_staticText821.Wrap( -1 )

		bSizer2721.Add( self.m_staticText821, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.table_collation = wx.TextCtrl( self.PanelTableOptions, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2721.Add( self.table_collation, 1, wx.ALL|wx.EXPAND, 5 )


		gSizer11.Add( bSizer2721, 0, wx.EXPAND, 5 )


		bSizer261.Add( gSizer11, 0, wx.EXPAND, 5 )


		self.PanelTableOptions.SetSizer( bSizer261 )
		self.PanelTableOptions.Layout()
		bSizer261.Fit( self.PanelTableOptions )
		self.m_notebook3.AddPage( self.PanelTableOptions, _(u"Options"), False )
		m_notebook3Bitmap = wx.Bitmap( u"icons/16x16/wrench.png", wx.BITMAP_TYPE_ANY )
		if ( m_notebook3Bitmap.IsOk() ):
			m_notebook3Images.Add( m_notebook3Bitmap )
			self.m_notebook3.SetPageImage( m_notebook3Index, m_notebook3Index )
			m_notebook3Index += 1

		self.PanelTableIndex = wx.Panel( self.m_notebook3, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer28 = wx.BoxSizer( wx.HORIZONTAL )


		self.PanelTableIndex.SetSizer( bSizer28 )
		self.PanelTableIndex.Layout()
		bSizer28.Fit( self.PanelTableIndex )
		self.m_notebook3.AddPage( self.PanelTableIndex, _(u"Indexes"), False )
		m_notebook3Bitmap = wx.Bitmap( u"icons/16x16/lightning.png", wx.BITMAP_TYPE_ANY )
		if ( m_notebook3Bitmap.IsOk() ):
			m_notebook3Images.Add( m_notebook3Bitmap )
			self.m_notebook3.SetPageImage( m_notebook3Index, m_notebook3Index )
			m_notebook3Index += 1


		bSizer55.Add( self.m_notebook3, 1, wx.EXPAND | wx.ALL, 5 )


		self.m_panel19.SetSizer( bSizer55 )
		self.m_panel19.Layout()
		bSizer55.Fit( self.m_panel19 )
		self.panel_table_columns = wx.Panel( self.m_splitter41, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.panel_table_columns.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

		bSizer54 = wx.BoxSizer( wx.VERTICAL )

		bSizer53 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText39 = wx.StaticText( self.panel_table_columns, wx.ID_ANY, _(u"Columns:"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText39.Wrap( -1 )

		bSizer53.Add( self.m_staticText39, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


		bSizer53.Add( ( 100, 0), 0, wx.EXPAND, 5 )

		self.btn_insert_column = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Insert"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_insert_column.SetBitmap( wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ) )
		bSizer53.Add( self.btn_insert_column, 0, wx.LEFT|wx.RIGHT, 2 )

		self.btn_column_delete = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Delete"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_column_delete.SetBitmap( wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ) )
		self.btn_column_delete.Enable( False )

		bSizer53.Add( self.btn_column_delete, 0, wx.LEFT|wx.RIGHT, 2 )

		self.btn_column_move_up = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Up"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_column_move_up.SetBitmap( wx.Bitmap( u"icons/16x16/arrow_up.png", wx.BITMAP_TYPE_ANY ) )
		self.btn_column_move_up.Enable( False )

		bSizer53.Add( self.btn_column_move_up, 0, wx.LEFT|wx.RIGHT, 2 )

		self.btn_column_move_down = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Down"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

		self.btn_column_move_down.SetBitmap( wx.Bitmap( u"icons/16x16/arrow_down.png", wx.BITMAP_TYPE_ANY ) )
		self.btn_column_move_down.Enable( False )

		bSizer53.Add( self.btn_column_move_down, 0, wx.LEFT|wx.RIGHT, 2 )


		bSizer53.Add( ( 0, 0), 1, wx.EXPAND, 5 )


		bSizer54.Add( bSizer53, 0, wx.ALL|wx.EXPAND, 5 )

		self.list_ctrl_table_columns = TableColumnsDataViewCtrl( self.panel_table_columns, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer54.Add( self.list_ctrl_table_columns, 1, wx.ALL|wx.EXPAND, 5 )

		bSizer52 = wx.BoxSizer( wx.HORIZONTAL )

		self.btn_table_delete = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Delete"), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer52.Add( self.btn_table_delete, 0, wx.ALL, 5 )

		self.btn_table_cancel = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Cancel"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.btn_table_cancel.Enable( False )

		bSizer52.Add( self.btn_table_cancel, 0, wx.ALL, 5 )

		self.btn_table_save = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Save"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.btn_table_save.Enable( False )

		bSizer52.Add( self.btn_table_save, 0, wx.ALL, 5 )


		bSizer54.Add( bSizer52, 0, wx.EXPAND, 5 )


		self.panel_table_columns.SetSizer( bSizer54 )
		self.panel_table_columns.Layout()
		bSizer54.Fit( self.panel_table_columns )
		self.menu_table_columns = wx.Menu()
		self.add_index = wx.MenuItem( self.menu_table_columns, wx.ID_ANY, _(u"Add Index"), wx.EmptyString, wx.ITEM_NORMAL )
		self.menu_table_columns.Append( self.add_index )

		self.m_menu21 = wx.Menu()
		self.m_menuItem8 = wx.MenuItem( self.m_menu21, wx.ID_ANY, _(u"Add PrimaryKey"), wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu21.Append( self.m_menuItem8 )

		self.m_menuItem9 = wx.MenuItem( self.m_menu21, wx.ID_ANY, _(u"Add Index"), wx.EmptyString, wx.ITEM_NORMAL )
		self.m_menu21.Append( self.m_menuItem9 )

		self.menu_table_columns.AppendSubMenu( self.m_menu21, _(u"MyMenu") )

		self.panel_table_columns.Bind( wx.EVT_RIGHT_DOWN, self.panel_table_columnsOnContextMenu )

		self.m_splitter41.SplitHorizontally( self.m_panel19, self.panel_table_columns, 200 )
		bSizer251.Add( self.m_splitter41, 1, wx.EXPAND, 0 )


		self.SetSizer( bSizer251 )
		self.Layout()

		# Connect Events
		self.btn_insert_column.Bind( wx.EVT_BUTTON, self.on_column_insert )
		self.btn_column_delete.Bind( wx.EVT_BUTTON, self.on_column_delete )
		self.btn_column_move_up.Bind( wx.EVT_BUTTON, self.on_column_move_up )
		self.btn_column_move_down.Bind( wx.EVT_BUTTON, self.on_column_move_down )
		self.btn_table_delete.Bind( wx.EVT_BUTTON, self.on_delete_table )
		self.btn_table_cancel.Bind( wx.EVT_BUTTON, self.do_cancel_table )
		self.btn_table_save.Bind( wx.EVT_BUTTON, self.do_save_table )

	def __del__( self ):
		pass


	# Virtual event handlers, override them in your derived class
	def on_column_insert( self, event ):
		event.Skip()

	def on_column_delete( self, event ):
		event.Skip()

	def on_column_move_up( self, event ):
		event.Skip()

	def on_column_move_down( self, event ):
		event.Skip()

	def on_delete_table( self, event ):
		event.Skip()

	def do_cancel_table( self, event ):
		event.Skip()

	def do_save_table( self, event ):
		event.Skip()

	def m_splitter41OnIdle( self, event ):
		self.m_splitter41.SetSashPosition( 200 )
		self.m_splitter41.Unbind( wx.EVT_IDLE )

	def panel_table_columnsOnContextMenu( self, event ):
		self.panel_table_columns.PopupMenu( self.menu_table_columns, event.GetPosition() )


