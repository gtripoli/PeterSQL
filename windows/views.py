# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 4.2.1-111-g5faebfea)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

from .components.dataview import TableIndexesDataViewCtrl
from .components.dataview import TableForeignKeysDataViewCtrl
from .components.dataview import TableCheckDataViewCtrl
from .components.dataview import TableColumnsDataViewCtrl
from .components.dataview import TableRecordsDataViewCtrl
from wx.lib.agw.flatnotebook import FlatNotebook
import wx
import wx.xrc
import wx.dataview
import wx.stc
import wx.lib.agw.hypertreelist

import gettext
_ = gettext.gettext

###########################################################################
## Class SplashScreen
###########################################################################

class SplashScreen ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 640,480 ), style = wx.FRAME_NO_TASKBAR|wx.STAY_ON_TOP|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer161 = wx.BoxSizer( wx.VERTICAL )

        self.m_bitmap3 = wx.StaticBitmap( self, wx.ID_ANY, wx.Bitmap( u"petersql_large.png", wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer161.Add( self.m_bitmap3, 1, wx.ALL|wx.EXPAND, 5 )

        self.m_gauge1 = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
        self.m_gauge1.SetValue( 0 )
        bSizer161.Add( self.m_gauge1, 0, wx.ALL|wx.EXPAND, 5 )


        self.SetSizer( bSizer161 )
        self.Layout()

        self.Centre( wx.BOTH )

    def __del__( self ):
        pass


###########################################################################
## Class ConnectionsDialog
###########################################################################

class ConnectionsDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = _(u"Connection"), pos = wx.DefaultPosition, size = wx.Size( 900,768 ), style = wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.RESIZE_BORDER )

        self.SetSizeHints( wx.Size( -1,-1 ), wx.DefaultSize )

        bSizer34 = wx.BoxSizer( wx.VERTICAL )

        self.m_splitter3 = wx.SplitterWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_LIVE_UPDATE )
        self.m_splitter3.Bind( wx.EVT_IDLE, self.m_splitter3OnIdle )
        self.m_splitter3.SetMinimumPaneSize( 250 )

        self.m_panel16 = wx.Panel( self.m_splitter3, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,-1 ), wx.TAB_TRAVERSAL )
        bSizer35 = wx.BoxSizer( wx.VERTICAL )

        self.connections_tree_ctrl = wx.dataview.DataViewCtrl( self.m_panel16, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.dataview.DV_ROW_LINES )
        self.connection_name = self.connections_tree_ctrl.AppendIconTextColumn( _(u"Name"), 0, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
        self.connection_last_connection = self.connections_tree_ctrl.AppendTextColumn( _(u"Last connection"), 1, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
        bSizer35.Add( self.connections_tree_ctrl, 1, wx.ALL|wx.EXPAND|wx.TOP, 5 )

        self.search_connection = wx.SearchCtrl( self.m_panel16, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.search_connection.ShowSearchButton( True )
        self.search_connection.ShowCancelButton( True )
        bSizer35.Add( self.search_connection, 0, wx.BOTTOM|wx.EXPAND|wx.LEFT|wx.RIGHT, 5 )


        self.m_panel16.SetSizer( bSizer35 )
        self.m_panel16.Layout()
        bSizer35.Fit( self.m_panel16 )
        self.connection_tree_menu = wx.Menu()
        self.m_menuItem4 = wx.MenuItem( self.connection_tree_menu, wx.ID_ANY, _(u"New directory"), wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menuItem4.SetBitmap( wx.Bitmap( u"icons/16x16/folder.png", wx.BITMAP_TYPE_ANY ) )
        self.connection_tree_menu.Append( self.m_menuItem4 )

        self.m_menuItem5 = wx.MenuItem( self.connection_tree_menu, wx.ID_ANY, _(u"New connection"), wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menuItem5.SetBitmap( wx.Bitmap( u"icons/16x16/server.png", wx.BITMAP_TYPE_ANY ) )
        self.connection_tree_menu.Append( self.m_menuItem5 )

        self.connection_tree_menu.AppendSeparator()

        self.m_menuItem18 = wx.MenuItem( self.connection_tree_menu, wx.ID_ANY, _(u"Rename"), wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menuItem18.SetBitmap( wx.Bitmap( u"icons/16x16/edit_marker.png", wx.BITMAP_TYPE_ANY ) )
        self.connection_tree_menu.Append( self.m_menuItem18 )
        self.m_menuItem18.Enable( False )

        self.m_menuItem19 = wx.MenuItem( self.connection_tree_menu, wx.ID_ANY, _(u"Clone connection"), wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menuItem19.SetBitmap( wx.Bitmap( u"icons/16x16/page_copy_columns.png", wx.BITMAP_TYPE_ANY ) )
        self.connection_tree_menu.Append( self.m_menuItem19 )
        self.m_menuItem19.Enable( False )

        self.m_menuItem21 = wx.MenuItem( self.connection_tree_menu, wx.ID_ANY, _(u"Delete"), wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menuItem21.SetBitmap( wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ) )
        self.connection_tree_menu.Append( self.m_menuItem21 )


        self.m_panel17 = wx.Panel( self.m_splitter3, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer36 = wx.BoxSizer( wx.VERTICAL )

        self.m_notebook4 = wx.Notebook( self.m_panel17, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.NB_FIXEDWIDTH )
        self.panel_connection = wx.Panel( self.m_notebook4, wx.ID_ANY, wx.DefaultPosition, wx.Size( 600,-1 ), wx.BORDER_NONE|wx.TAB_TRAVERSAL )
        self.panel_connection.SetMinSize( wx.Size( 600,-1 ) )

        bSizer12 = wx.BoxSizer( wx.VERTICAL )

        bSizer1211 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText211 = wx.StaticText( self.panel_connection, wx.ID_ANY, _(u"Name"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText211.Wrap( -1 )

        bSizer1211.Add( self.m_staticText211, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.name = wx.TextCtrl( self.panel_connection, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer1211.Add( self.name, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        bSizer12.Add( bSizer1211, 0, wx.EXPAND, 5 )

        bSizer13 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer13.SetMinSize( wx.Size( -1,0 ) )
        self.m_staticText2 = wx.StaticText( self.panel_connection, wx.ID_ANY, _(u"Engine"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText2.Wrap( -1 )

        bSizer13.Add( self.m_staticText2, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        engineChoices = []
        self.engine = wx.Choice( self.panel_connection, wx.ID_ANY, wx.DefaultPosition, wx.Size( 400,-1 ), engineChoices, 0 )
        self.engine.SetSelection( 0 )
        bSizer13.Add( self.engine, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        bSizer12.Add( bSizer13, 0, wx.EXPAND, 5 )

        self.m_staticline41 = wx.StaticLine( self.panel_connection, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        bSizer12.Add( self.m_staticline41, 0, wx.EXPAND | wx.ALL, 5 )

        self.panel_credentials = wx.Panel( self.panel_connection, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer103 = wx.BoxSizer( wx.VERTICAL )

        bSizer121 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText21 = wx.StaticText( self.panel_credentials, wx.ID_ANY, _(u"Host + port"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText21.Wrap( -1 )

        bSizer121.Add( self.m_staticText21, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.hostname = wx.TextCtrl( self.panel_credentials, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer121.Add( self.hostname, 1, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.port = wx.SpinCtrl( self.panel_credentials, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 65536, 3306 )
        bSizer121.Add( self.port, 0, wx.ALL, 5 )


        bSizer103.Add( bSizer121, 0, wx.EXPAND, 5 )

        bSizer122 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText22 = wx.StaticText( self.panel_credentials, wx.ID_ANY, _(u"Username"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText22.Wrap( -1 )

        bSizer122.Add( self.m_staticText22, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.username = wx.TextCtrl( self.panel_credentials, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer122.Add( self.username, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


        bSizer103.Add( bSizer122, 0, wx.EXPAND, 5 )

        bSizer1221 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText221 = wx.StaticText( self.panel_credentials, wx.ID_ANY, _(u"Password"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText221.Wrap( -1 )

        bSizer1221.Add( self.m_staticText221, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.password = wx.TextCtrl( self.panel_credentials, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_PASSWORD )
        bSizer1221.Add( self.password, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


        bSizer103.Add( bSizer1221, 0, wx.EXPAND, 5 )

        bSizer159 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText84 = wx.StaticText( self.panel_credentials, wx.ID_ANY, _(u"Connection timeout"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText84.Wrap( -1 )

        self.m_staticText84.SetMinSize( wx.Size( 150,-1 ) )

        bSizer159.Add( self.m_staticText84, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.connection_timeout = wx.SpinCtrl( self.panel_credentials, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 60, 10 )
        bSizer159.Add( self.connection_timeout, 1, wx.ALL, 5 )


        bSizer103.Add( bSizer159, 1, wx.EXPAND, 5 )

        bSizer116 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer116.Add( ( 156, 0), 0, wx.EXPAND, 5 )

        self.use_tls = wx.CheckBox( self.panel_credentials, wx.ID_ANY, _(u"Use TLS"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer116.Add( self.use_tls, 0, wx.ALL, 5 )


        bSizer103.Add( bSizer116, 0, wx.EXPAND, 5 )

        bSizer1631 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer1631.Add( ( 156, 0), 0, wx.EXPAND, 5 )

        self.read_only = wx.CheckBox( self.panel_credentials, wx.ID_ANY, _(u"Mark read only"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer1631.Add( self.read_only, 0, wx.ALL, 5 )


        bSizer103.Add( bSizer1631, 0, wx.EXPAND, 5 )

        bSizer163 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer163.Add( ( 156, 0), 0, wx.EXPAND, 5 )

        self.ssh_tunnel_enabled = wx.CheckBox( self.panel_credentials, wx.ID_ANY, _(u"Use SSH tunnel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer163.Add( self.ssh_tunnel_enabled, 0, wx.ALL, 5 )


        bSizer103.Add( bSizer163, 0, wx.EXPAND, 5 )

        bSizer164 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer164.Add( ( 156, 0), 0, wx.EXPAND, 5 )

        self.compressed_protocol = wx.CheckBox( self.panel_credentials, wx.ID_ANY, _(u"Compressed client/server protocol"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer164.Add( self.compressed_protocol, 0, wx.ALIGN_CENTER|wx.ALL, 5 )


        bSizer103.Add( bSizer164, 0, wx.EXPAND, 5 )


        self.panel_credentials.SetSizer( bSizer103 )
        self.panel_credentials.Layout()
        bSizer103.Fit( self.panel_credentials )
        bSizer12.Add( self.panel_credentials, 0, wx.EXPAND | wx.ALL, 0 )

        self.panel_source = wx.Panel( self.panel_connection, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.panel_source.Hide()

        bSizer105 = wx.BoxSizer( wx.VERTICAL )

        bSizer106 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText50 = wx.StaticText( self.panel_source, wx.ID_ANY, _(u"Filename"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText50.Wrap( -1 )

        bSizer106.Add( self.m_staticText50, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.filename = wx.FilePickerCtrl( self.panel_source, wx.ID_ANY, wx.EmptyString, _(u"Select a file"), _(u"*.*"), wx.DefaultPosition, wx.DefaultSize, wx.FLP_CHANGE_DIR|wx.FLP_DEFAULT_STYLE|wx.FLP_FILE_MUST_EXIST )
        bSizer106.Add( self.filename, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        bSizer105.Add( bSizer106, 1, wx.EXPAND, 5 )


        self.panel_source.SetSizer( bSizer105 )
        self.panel_source.Layout()
        bSizer105.Fit( self.panel_source )
        bSizer12.Add( self.panel_source, 0, wx.EXPAND | wx.ALL, 0 )

        self.m_staticline5 = wx.StaticLine( self.panel_connection, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        bSizer12.Add( self.m_staticline5, 0, wx.EXPAND | wx.ALL, 5 )

        bSizer122111 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText22111 = wx.StaticText( self.panel_connection, wx.ID_ANY, _(u"Comments"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText22111.Wrap( -1 )

        bSizer122111.Add( self.m_staticText22111, 0, wx.ALL, 5 )

        self.comments = wx.TextCtrl( self.panel_connection, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,200 ), wx.TE_MULTILINE )
        bSizer122111.Add( self.comments, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer12.Add( bSizer122111, 0, wx.EXPAND, 5 )


        self.panel_connection.SetSizer( bSizer12 )
        self.panel_connection.Layout()
        self.m_notebook4.AddPage( self.panel_connection, _(u"Settings"), True )
        self.panel_ssh_tunnel = wx.Panel( self.m_notebook4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.panel_ssh_tunnel.Enable( False )

        bSizer102 = wx.BoxSizer( wx.VERTICAL )

        bSizer1213 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText213 = wx.StaticText( self.panel_ssh_tunnel, wx.ID_ANY, _(u"SSH executable"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText213.Wrap( -1 )

        bSizer1213.Add( self.m_staticText213, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.ssh_tunnel_executable = wx.TextCtrl( self.panel_ssh_tunnel, wx.ID_ANY, _(u"ssh"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer1213.Add( self.ssh_tunnel_executable, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        bSizer102.Add( bSizer1213, 0, wx.EXPAND, 5 )

        bSizer12131 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText2131 = wx.StaticText( self.panel_ssh_tunnel, wx.ID_ANY, _(u"SSH host + port"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText2131.Wrap( -1 )

        bSizer12131.Add( self.m_staticText2131, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.ssh_tunnel_hostname = wx.TextCtrl( self.panel_ssh_tunnel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer12131.Add( self.ssh_tunnel_hostname, 1, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.ssh_tunnel_port = wx.SpinCtrl( self.panel_ssh_tunnel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 65536, 22 )
        bSizer12131.Add( self.ssh_tunnel_port, 0, wx.ALL, 5 )

        self.m_bitmap11 = wx.StaticBitmap( self.panel_ssh_tunnel, wx.ID_ANY, wx.Bitmap( u"icons/16x16/information.png", wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_bitmap11.SetToolTip( _(u"SSH host + port (the SSH server that forwards traffic to the DB)") )

        bSizer12131.Add( self.m_bitmap11, 0, wx.ALL|wx.EXPAND, 5 )


        bSizer102.Add( bSizer12131, 0, wx.EXPAND, 5 )

        bSizer12132 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText2132 = wx.StaticText( self.panel_ssh_tunnel, wx.ID_ANY, _(u"SSH username"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText2132.Wrap( -1 )

        bSizer12132.Add( self.m_staticText2132, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.ssh_tunnel_username = wx.TextCtrl( self.panel_ssh_tunnel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer12132.Add( self.ssh_tunnel_username, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        bSizer102.Add( bSizer12132, 0, wx.EXPAND, 5 )

        bSizer121321 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText21321 = wx.StaticText( self.panel_ssh_tunnel, wx.ID_ANY, _(u"SSH password"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText21321.Wrap( -1 )

        bSizer121321.Add( self.m_staticText21321, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.ssh_tunnel_password = wx.TextCtrl( self.panel_ssh_tunnel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_PASSWORD )
        bSizer121321.Add( self.ssh_tunnel_password, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        bSizer102.Add( bSizer121321, 0, wx.EXPAND, 5 )

        bSizer1213211 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText213211 = wx.StaticText( self.panel_ssh_tunnel, wx.ID_ANY, _(u"Local port"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText213211.Wrap( -1 )

        bSizer1213211.Add( self.m_staticText213211, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.ssh_tunnel_local_port = wx.SpinCtrl( self.panel_ssh_tunnel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 65536, 0 )
        self.ssh_tunnel_local_port.SetToolTip( _(u"if the value is set to 0, the first available port will be used") )

        bSizer1213211.Add( self.ssh_tunnel_local_port, 1, wx.ALL, 5 )


        bSizer102.Add( bSizer1213211, 0, wx.EXPAND, 5 )

        bSizer1213212 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText213212 = wx.StaticText( self.panel_ssh_tunnel, wx.ID_ANY, _(u"Identity file"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText213212.Wrap( -1 )

        bSizer1213212.Add( self.m_staticText213212, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.identity_file = wx.FilePickerCtrl( self.panel_ssh_tunnel, wx.ID_ANY, wx.EmptyString, _(u"Select a file"), _(u"*.*"), wx.DefaultPosition, wx.DefaultSize, wx.FLP_CHANGE_DIR|wx.FLP_DEFAULT_STYLE|wx.FLP_FILE_MUST_EXIST )
        bSizer1213212.Add( self.identity_file, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        bSizer102.Add( bSizer1213212, 0, wx.EXPAND, 5 )

        self.m_staticline6 = wx.StaticLine( self.panel_ssh_tunnel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
        bSizer102.Add( self.m_staticline6, 0, wx.EXPAND | wx.ALL, 5 )

        bSizer121311 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText21311 = wx.StaticText( self.panel_ssh_tunnel, wx.ID_ANY, _(u"Remote host + port"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText21311.Wrap( -1 )

        bSizer121311.Add( self.m_staticText21311, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.remote_hostname = wx.TextCtrl( self.panel_ssh_tunnel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer121311.Add( self.remote_hostname, 1, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.remote_port = wx.SpinCtrl( self.panel_ssh_tunnel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 65536, 3306 )
        bSizer121311.Add( self.remote_port, 0, wx.ALL, 5 )

        self.m_bitmap1 = wx.StaticBitmap( self.panel_ssh_tunnel, wx.ID_ANY, wx.Bitmap( u"icons/16x16/information.png", wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_bitmap1.SetToolTip( _(u"Remote host/port is the real DB target (defaults to DB Host/Port).") )

        bSizer121311.Add( self.m_bitmap1, 0, wx.ALL|wx.EXPAND, 5 )


        bSizer102.Add( bSizer121311, 0, wx.EXPAND, 5 )

        bSizer121322 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText21322 = wx.StaticText( self.panel_ssh_tunnel, wx.ID_ANY, _(u"SSH extra args"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText21322.Wrap( -1 )

        bSizer121322.Add( self.m_staticText21322, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.ssh_tunnel_extra_args = wx.TextCtrl( self.panel_ssh_tunnel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer121322.Add( self.ssh_tunnel_extra_args, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        bSizer102.Add( bSizer121322, 0, wx.EXPAND, 5 )


        self.panel_ssh_tunnel.SetSizer( bSizer102 )
        self.panel_ssh_tunnel.Layout()
        bSizer102.Fit( self.panel_ssh_tunnel )
        self.m_notebook4.AddPage( self.panel_ssh_tunnel, _(u"SSH Tunnel"), False )
        self.panel_statistics = wx.Panel( self.m_notebook4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer361 = wx.BoxSizer( wx.VERTICAL )

        bSizer37 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText15 = wx.StaticText( self.panel_statistics, wx.ID_ANY, _(u"Created at"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText15.Wrap( -1 )

        self.m_staticText15.SetMinSize( wx.Size( 200,-1 ) )

        bSizer37.Add( self.m_staticText15, 0, wx.ALL, 5 )

        self.created_at = wx.StaticText( self.panel_statistics, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.created_at.Wrap( -1 )

        bSizer37.Add( self.created_at, 0, wx.ALL, 5 )


        bSizer361.Add( bSizer37, 0, wx.EXPAND, 5 )

        bSizer371 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText151 = wx.StaticText( self.panel_statistics, wx.ID_ANY, _(u"Last connection"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText151.Wrap( -1 )

        self.m_staticText151.SetMinSize( wx.Size( 200,-1 ) )

        bSizer371.Add( self.m_staticText151, 0, wx.ALL, 5 )

        self.last_connection_at = wx.StaticText( self.panel_statistics, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.last_connection_at.Wrap( -1 )

        bSizer371.Add( self.last_connection_at, 0, wx.ALL, 5 )


        bSizer361.Add( bSizer371, 0, wx.EXPAND, 5 )

        bSizer3711 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText1511 = wx.StaticText( self.panel_statistics, wx.ID_ANY, _(u"Successful connections"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1511.Wrap( -1 )

        self.m_staticText1511.SetMinSize( wx.Size( 200,-1 ) )

        bSizer3711.Add( self.m_staticText1511, 0, wx.ALL, 5 )

        self.successful_connected = wx.StaticText( self.panel_statistics, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.successful_connected.Wrap( -1 )

        bSizer3711.Add( self.successful_connected, 0, wx.ALL, 5 )


        bSizer361.Add( bSizer3711, 0, wx.EXPAND, 5 )

        bSizer371111 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText151111 = wx.StaticText( self.panel_statistics, wx.ID_ANY, _(u"Last successful connection"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText151111.Wrap( -1 )

        self.m_staticText151111.SetMinSize( wx.Size( 200,-1 ) )

        bSizer371111.Add( self.m_staticText151111, 0, wx.ALL, 5 )

        self.last_successful_connection = wx.StaticText( self.panel_statistics, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.last_successful_connection.Wrap( -1 )

        bSizer371111.Add( self.last_successful_connection, 1, wx.ALL, 5 )


        bSizer361.Add( bSizer371111, 0, wx.EXPAND, 5 )

        bSizer37111 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText15111 = wx.StaticText( self.panel_statistics, wx.ID_ANY, _(u"Unsuccessful connections"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText15111.Wrap( -1 )

        self.m_staticText15111.SetMinSize( wx.Size( 200,-1 ) )

        bSizer37111.Add( self.m_staticText15111, 0, wx.ALL, 5 )

        self.unsuccessful_connections = wx.StaticText( self.panel_statistics, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.unsuccessful_connections.Wrap( -1 )

        bSizer37111.Add( self.unsuccessful_connections, 0, wx.ALL, 5 )


        bSizer361.Add( bSizer37111, 0, wx.EXPAND, 5 )

        bSizer371112 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText151112 = wx.StaticText( self.panel_statistics, wx.ID_ANY, _(u"Last failure reason"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText151112.Wrap( -1 )

        self.m_staticText151112.SetMinSize( wx.Size( 200,-1 ) )

        bSizer371112.Add( self.m_staticText151112, 0, wx.ALL, 5 )

        self.last_failure_raison = wx.StaticText( self.panel_statistics, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.last_failure_raison.Wrap( -1 )

        bSizer371112.Add( self.last_failure_raison, 1, wx.ALL, 5 )


        bSizer361.Add( bSizer371112, 0, wx.EXPAND, 5 )

        bSizer3711121 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText1511121 = wx.StaticText( self.panel_statistics, wx.ID_ANY, _(u"Total connection attempts"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1511121.Wrap( -1 )

        self.m_staticText1511121.SetMinSize( wx.Size( 200,-1 ) )

        bSizer3711121.Add( self.m_staticText1511121, 0, wx.ALL, 5 )

        self.total_connection_attempts = wx.StaticText( self.panel_statistics, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.total_connection_attempts.Wrap( -1 )

        bSizer3711121.Add( self.total_connection_attempts, 1, wx.ALL, 5 )


        bSizer361.Add( bSizer3711121, 0, wx.EXPAND, 5 )

        bSizer37111211 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText15111211 = wx.StaticText( self.panel_statistics, wx.ID_ANY, _(u"Average connection time (ms)"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText15111211.Wrap( -1 )

        self.m_staticText15111211.SetMinSize( wx.Size( 200,-1 ) )

        bSizer37111211.Add( self.m_staticText15111211, 0, wx.ALL, 5 )

        self.average_connection_time = wx.StaticText( self.panel_statistics, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.average_connection_time.Wrap( -1 )

        bSizer37111211.Add( self.average_connection_time, 1, wx.ALL, 5 )


        bSizer361.Add( bSizer37111211, 0, wx.EXPAND, 5 )

        bSizer371112111 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText151112111 = wx.StaticText( self.panel_statistics, wx.ID_ANY, _(u"Most recent connection duration"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText151112111.Wrap( -1 )

        self.m_staticText151112111.SetMinSize( wx.Size( 200,-1 ) )

        bSizer371112111.Add( self.m_staticText151112111, 0, wx.ALL, 5 )

        self.most_recent_connection_duration = wx.StaticText( self.panel_statistics, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.most_recent_connection_duration.Wrap( -1 )

        bSizer371112111.Add( self.most_recent_connection_duration, 1, wx.ALL, 5 )


        bSizer361.Add( bSizer371112111, 0, wx.EXPAND, 5 )


        self.panel_statistics.SetSizer( bSizer361 )
        self.panel_statistics.Layout()
        bSizer361.Fit( self.panel_statistics )
        self.m_notebook4.AddPage( self.panel_statistics, _(u"Statistics"), False )

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

        self.btn_create.SetBitmap( wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ) )
        self.m_menu12 = wx.Menu()
        self.m_menuItem16 = wx.MenuItem( self.m_menu12, wx.ID_ANY, _(u"Create connection"), wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menu12.Append( self.m_menuItem16 )

        self.m_menuItem17 = wx.MenuItem( self.m_menu12, wx.ID_ANY, _(u"Create directory"), wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menu12.Append( self.m_menuItem17 )

        self.btn_create.Bind( wx.EVT_RIGHT_DOWN, self.btn_createOnContextMenu )

        bSizer301.Add( self.btn_create, 0, wx.ALL|wx.BOTTOM, 5 )

        self.btn_create_directory = wx.Button( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.BU_EXACTFIT|wx.BU_NOTEXT )

        self.btn_create_directory.SetBitmap( wx.Bitmap( u"icons/16x16/folder.png", wx.BITMAP_TYPE_ANY ) )
        bSizer301.Add( self.btn_create_directory, 0, wx.ALL, 5 )

        self.btn_delete = wx.Button( self, wx.ID_ANY, _(u"Delete"), wx.DefaultPosition, wx.DefaultSize, 0 )

        self.btn_delete.SetBitmap( wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ) )
        self.btn_delete.Enable( False )

        bSizer301.Add( self.btn_delete, 0, wx.ALL, 5 )


        bSizer28.Add( bSizer301, 1, wx.EXPAND, 5 )

        bSizer110 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer28.Add( bSizer110, 1, wx.EXPAND, 5 )

        bSizer29 = wx.BoxSizer( wx.HORIZONTAL )

        self.btn_cancel = wx.Button( self, wx.ID_ANY, _(u"Cancel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_cancel.Hide()

        bSizer29.Add( self.btn_cancel, 0, wx.ALL, 5 )

        self.btn_save = wx.Button( self, wx.ID_ANY, _(u"Save"), wx.DefaultPosition, wx.DefaultSize, 0 )

        self.btn_save.SetBitmap( wx.Bitmap( u"icons/16x16/disk.png", wx.BITMAP_TYPE_ANY ) )
        self.btn_save.Enable( False )

        bSizer29.Add( self.btn_save, 0, wx.ALL, 5 )

        self.btn_test = wx.Button( self, wx.ID_ANY, _(u"Test"), wx.DefaultPosition, wx.DefaultSize, 0 )

        self.btn_test.SetBitmap( wx.Bitmap( u"icons/16x16/world_go.png", wx.BITMAP_TYPE_ANY ) )
        self.btn_test.Enable( False )

        bSizer29.Add( self.btn_test, 0, wx.ALL, 5 )

        self.btn_open = wx.Button( self, wx.ID_ANY, _(u"Connect"), wx.DefaultPosition, wx.DefaultSize, 0 )

        self.btn_open.SetBitmap( wx.Bitmap( u"icons/16x16/server_go.png", wx.BITMAP_TYPE_ANY ) )
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
        self.Bind( wx.EVT_MENU, self.on_new_connection, id = self.m_menuItem5.GetId() )
        self.Bind( wx.EVT_MENU, self.on_rename, id = self.m_menuItem18.GetId() )
        self.Bind( wx.EVT_MENU, self.on_clone_connection, id = self.m_menuItem19.GetId() )
        self.Bind( wx.EVT_MENU, self.on_delete, id = self.m_menuItem21.GetId() )
        self.engine.Bind( wx.EVT_CHOICE, self.on_choice_engine )
        self.btn_create.Bind( wx.EVT_BUTTON, self.on_create )
        self.btn_create_directory.Bind( wx.EVT_BUTTON, self.on_create_directory )
        self.btn_delete.Bind( wx.EVT_BUTTON, self.on_delete )
        self.btn_save.Bind( wx.EVT_BUTTON, self.on_save )
        self.btn_test.Bind( wx.EVT_BUTTON, self.on_test_session )
        self.btn_open.Bind( wx.EVT_BUTTON, self.on_connect )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def on_close( self, event ):
        event.Skip()

    def on_new_directory( self, event ):
        event.Skip()

    def on_new_connection( self, event ):
        event.Skip()

    def on_rename( self, event ):
        event.Skip()

    def on_clone_connection( self, event ):
        event.Skip()

    def on_delete( self, event ):
        event.Skip()

    def on_choice_engine( self, event ):
        event.Skip()

    def on_create( self, event ):
        event.Skip()

    def on_create_directory( self, event ):
        event.Skip()


    def on_save( self, event ):
        event.Skip()

    def on_test_session( self, event ):
        event.Skip()

    def on_connect( self, event ):
        event.Skip()

    def m_splitter3OnIdle( self, event ):
        self.m_splitter3.SetSashPosition( 250 )
        self.m_splitter3.Unbind( wx.EVT_IDLE )

    def btn_createOnContextMenu( self, event ):
        self.btn_create.PopupMenu( self.m_menu12, event.GetPosition() )


###########################################################################
## Class SettingsDialog
###########################################################################

class SettingsDialog ( wx.Dialog ):

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
## Class ColumnContentDialog
###########################################################################

class ColumnContentDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = _(u"Column content"), pos = wx.DefaultPosition, size = wx.Size( 900,550 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.Size( 640,480 ), wx.DefaultSize )

        bSizer111 = wx.BoxSizer( wx.VERTICAL )

        bSizer112 = wx.BoxSizer( wx.VERTICAL )

        bSizer113 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText51 = wx.StaticText( self, wx.ID_ANY, _(u"Syntax"), wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        self.m_staticText51.Wrap( -1 )

        bSizer113.Add( self.m_staticText51, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        syntax_choiceChoices = []
        self.syntax_choice = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, syntax_choiceChoices, 0 )
        self.syntax_choice.SetSelection( 0 )
        bSizer113.Add( self.syntax_choice, 0, wx.ALL, 5 )


        bSizer112.Add( bSizer113, 1, wx.EXPAND, 5 )


        bSizer111.Add( bSizer112, 0, wx.EXPAND, 5 )

        self.advanced_stc_editor = wx.stc.StyledTextCtrl( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        self.advanced_stc_editor.SetUseTabs ( False )
        self.advanced_stc_editor.SetTabWidth ( 4 )
        self.advanced_stc_editor.SetIndent ( 4 )
        self.advanced_stc_editor.SetTabIndents( True )
        self.advanced_stc_editor.SetBackSpaceUnIndents( True )
        self.advanced_stc_editor.SetViewEOL( False )
        self.advanced_stc_editor.SetViewWhiteSpace( False )
        self.advanced_stc_editor.SetMarginWidth( 2, 0 )
        self.advanced_stc_editor.SetIndentationGuides( True )
        self.advanced_stc_editor.SetReadOnly( False )
        self.advanced_stc_editor.SetMarginWidth( 1, 0 )
        self.advanced_stc_editor.SetMarginType( 0, wx.stc.STC_MARGIN_NUMBER )
        self.advanced_stc_editor.SetMarginWidth( 0, self.advanced_stc_editor.TextWidth( wx.stc.STC_STYLE_LINENUMBER, "_99999" ) )
        self.advanced_stc_editor.MarkerDefine( wx.stc.STC_MARKNUM_FOLDER, wx.stc.STC_MARK_BOXPLUS )
        self.advanced_stc_editor.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDER, wx.BLACK)
        self.advanced_stc_editor.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDER, wx.WHITE)
        self.advanced_stc_editor.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.stc.STC_MARK_BOXMINUS )
        self.advanced_stc_editor.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.BLACK )
        self.advanced_stc_editor.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.WHITE )
        self.advanced_stc_editor.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERSUB, wx.stc.STC_MARK_EMPTY )
        self.advanced_stc_editor.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEREND, wx.stc.STC_MARK_BOXPLUS )
        self.advanced_stc_editor.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEREND, wx.BLACK )
        self.advanced_stc_editor.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEREND, wx.WHITE )
        self.advanced_stc_editor.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.stc.STC_MARK_BOXMINUS )
        self.advanced_stc_editor.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.BLACK)
        self.advanced_stc_editor.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.WHITE)
        self.advanced_stc_editor.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERMIDTAIL, wx.stc.STC_MARK_EMPTY )
        self.advanced_stc_editor.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERTAIL, wx.stc.STC_MARK_EMPTY )
        self.advanced_stc_editor.SetSelBackground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT ) )
        self.advanced_stc_editor.SetSelForeground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT ) )
        bSizer111.Add( self.advanced_stc_editor, 1, wx.EXPAND | wx.ALL, 5 )

        bSizer114 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer114.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.m_button49 = wx.Button( self, wx.ID_ANY, _(u"Cancel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer114.Add( self.m_button49, 0, wx.ALL, 5 )

        self.m_button48 = wx.Button( self, wx.ID_ANY, _(u"Ok"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer114.Add( self.m_button48, 0, wx.ALL, 5 )


        bSizer111.Add( bSizer114, 0, wx.EXPAND, 5 )


        self.SetSizer( bSizer111 )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.syntax_choice.Bind( wx.EVT_CHOICE, self.on_syntax_changed )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def on_syntax_changed( self, event ):
        event.Skip()


###########################################################################
## Class MainFrameView
###########################################################################

class MainFrameView ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = _(u"PeterSQL"), pos = wx.DefaultPosition, size = wx.Size( 1280,1024 ), style = wx.DEFAULT_FRAME_STYLE|wx.MAXIMIZE_BOX|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.Size( 800,600 ), wx.DefaultSize )

        self.m_menubar2 = wx.MenuBar( 0 )
        self.m_menu2 = wx.Menu()
        self.m_menuItem22 = wx.MenuItem( self.m_menu2, wx.ID_ANY, _(u"Settings"), wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menu2.Append( self.m_menuItem22 )

        self.m_menubar2.Append( self.m_menu2, _(u"File") )

        self.m_menu4 = wx.Menu()
        self.m_menuItem15 = wx.MenuItem( self.m_menu4, wx.ID_ANY, _(u"About"), wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menu4.Append( self.m_menuItem15 )

        self.m_menubar2.Append( self.m_menu4, _(u"Help") )

        self.SetMenuBar( self.m_menubar2 )

        self.m_toolBar1 = self.CreateToolBar( wx.TB_HORIZONTAL, wx.ID_ANY )
        self.m_tool5 = self.m_toolBar1.AddTool( wx.ID_ANY, _(u"Open connection manager"), wx.Bitmap( u"icons/16x16/server_connect.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_toolBar1.AddSeparator()

        self.m_tool4 = self.m_toolBar1.AddTool( wx.ID_ANY, _(u"Disconnect from server"), wx.Bitmap( u"icons/16x16/disconnect.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.tool_refresh_database = self.m_toolBar1.AddTool( wx.ID_ANY, _(u"tool"), wx.Bitmap( u"icons/16x16/database_refresh.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Refresh"), _(u"Refresh"), None )

        self.m_toolBar1.AddSeparator()

        self.tool_add_database = self.m_toolBar1.AddTool( wx.ID_ANY, _(u"Add"), wx.Bitmap( u"icons/16x16/database_add.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.database_delete = self.m_toolBar1.AddTool( wx.ID_ANY, _(u"Add"), wx.Bitmap( u"icons/16x16/database_delete.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_toolBar1.AddSeparator()


        self.m_toggleBtn1 = wx.ToggleButton( self.m_toolBar1, wx.ID_ANY, _(u"{mode}"), wx.DefaultPosition, wx.DefaultSize, 0 )

        self.m_toggleBtn1.SetBitmap( wx.Bitmap( u"icons/16x16/lock.png", wx.BITMAP_TYPE_ANY ) )
        self.m_toggleBtn1.SetBitmapPressed( wx.Bitmap( u"icons/16x16/bullet_green.png", wx.BITMAP_TYPE_ANY ) )
        self.m_toolBar1.AddControl( self.m_toggleBtn1 )
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

        self.m_panel14 = wx.Panel( self.m_splitter4, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.FULL_REPAINT_ON_RESIZE|wx.TAB_TRAVERSAL )
        bSizer24 = wx.BoxSizer( wx.HORIZONTAL )

        self.tree_ctrl_explorer = wx.lib.agw.hypertreelist.HyperTreeList(
        self.m_panel14, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
        agwStyle=wx.TR_DEFAULT_STYLE|wx.TR_SINGLE|wx.TR_FULL_ROW_HIGHLIGHT|wx.TR_HIDE_ROOT|wx.TR_LINES_AT_ROOT
        )
        bSizer24.Add( self.tree_ctrl_explorer, 1, wx.ALL|wx.EXPAND, 5 )


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
        bSizer27 = wx.BoxSizer( wx.VERTICAL )

        self.m_splitter7 = wx.SplitterWindow( self.panel_database, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_3D )
        self.m_splitter7.Bind( wx.EVT_IDLE, self.m_splitter7OnIdle )
        self.m_splitter7.SetMinimumPaneSize( 200 )

        self.m_panel54 = wx.Panel( self.m_splitter7, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer158 = wx.BoxSizer( wx.VERTICAL )

        self.m_notebook6 = wx.Notebook( self.m_panel54, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_panel30 = wx.Panel( self.m_notebook6, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer171 = wx.BoxSizer( wx.VERTICAL )

        bSizer159 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText90 = wx.StaticText( self.m_panel30, wx.ID_ANY, _(u"Name"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText90.Wrap( -1 )

        self.m_staticText90.SetMinSize( wx.Size( 150,-1 ) )

        bSizer159.Add( self.m_staticText90, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.database_name = wx.TextCtrl( self.m_panel30, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_READONLY )
        bSizer159.Add( self.database_name, 1, wx.ALL, 5 )


        bSizer171.Add( bSizer159, 0, wx.EXPAND, 5 )

        bSizer142 = wx.BoxSizer( wx.HORIZONTAL )

        self.database_collation_panel = wx.Panel( self.m_panel30, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer1392 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText702 = wx.StaticText( self.database_collation_panel, wx.ID_ANY, _(u"Collation"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText702.Wrap( -1 )

        self.m_staticText702.SetMinSize( wx.Size( 150,-1 ) )

        bSizer1392.Add( self.m_staticText702, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        database_collationChoices = []
        self.database_collation = wx.Choice( self.database_collation_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, database_collationChoices, 0 )
        self.database_collation.SetSelection( 0 )
        bSizer1392.Add( self.database_collation, 1, wx.ALL, 5 )


        self.database_collation_panel.SetSizer( bSizer1392 )
        self.database_collation_panel.Layout()
        bSizer1392.Fit( self.database_collation_panel )
        bSizer142.Add( self.database_collation_panel, 1, wx.ALIGN_CENTER, 5 )


        bSizer171.Add( bSizer142, 0, wx.EXPAND, 5 )

        bSizer13911 = wx.BoxSizer( wx.HORIZONTAL )

        self.database_connection_limit_panel = wx.Panel( self.m_panel30, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer139111 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText70111 = wx.StaticText( self.database_connection_limit_panel, wx.ID_ANY, _(u"Connection limit"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText70111.Wrap( -1 )

        self.m_staticText70111.SetMinSize( wx.Size( 150,-1 ) )

        bSizer139111.Add( self.m_staticText70111, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.database_connection_limit = wx.SpinCtrl( self.database_connection_limit_panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 0, 0 )
        bSizer139111.Add( self.database_connection_limit, 1, wx.ALL, 5 )


        self.database_connection_limit_panel.SetSizer( bSizer139111 )
        self.database_connection_limit_panel.Layout()
        bSizer139111.Fit( self.database_connection_limit_panel )
        bSizer13911.Add( self.database_connection_limit_panel, 1, wx.ALIGN_CENTER, 5 )

        self.database_encryption_panel = wx.Panel( self.m_panel30, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer1391 = wx.BoxSizer( wx.HORIZONTAL )

        self.database_encryption = wx.CheckBox( self.database_encryption_panel, wx.ID_ANY, _(u"Encryption"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer1391.Add( self.database_encryption, 0, wx.ALL|wx.EXPAND, 5 )


        self.database_encryption_panel.SetSizer( bSizer1391 )
        self.database_encryption_panel.Layout()
        bSizer1391.Fit( self.database_encryption_panel )
        bSizer13911.Add( self.database_encryption_panel, 0, wx.ALIGN_CENTER, 0 )


        bSizer171.Add( bSizer13911, 0, wx.EXPAND, 5 )


        self.m_panel30.SetSizer( bSizer171 )
        self.m_panel30.Layout()
        bSizer171.Fit( self.m_panel30 )
        self.m_notebook6.AddPage( self.m_panel30, _(u"General"), True )
        self.m_panel31 = wx.Panel( self.m_notebook6, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_panel31.Hide()

        bSizer82 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText7011 = wx.StaticText( self.m_panel31, wx.ID_ANY, _(u"MyLabel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText7011.Wrap( -1 )

        self.m_staticText7011.SetMinSize( wx.Size( 150,-1 ) )

        bSizer82.Add( self.m_staticText7011, 0, wx.ALL, 5 )

        self.m_staticText7011111 = wx.StaticText( self.m_panel31, wx.ID_ANY, _(u"MyLabel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText7011111.Wrap( -1 )

        self.m_staticText7011111.SetMinSize( wx.Size( 150,-1 ) )

        bSizer82.Add( self.m_staticText7011111, 0, wx.ALL, 5 )

        self.m_staticText70111111 = wx.StaticText( self.m_panel31, wx.ID_ANY, _(u"MyLabel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText70111111.Wrap( -1 )

        self.m_staticText70111111.SetMinSize( wx.Size( 150,-1 ) )

        bSizer82.Add( self.m_staticText70111111, 0, wx.ALL, 5 )


        self.m_panel31.SetSizer( bSizer82 )
        self.m_panel31.Layout()
        bSizer82.Fit( self.m_panel31 )
        self.m_notebook6.AddPage( self.m_panel31, _(u"Diagram"), False )
        self.m_panel801 = wx.Panel( self.m_notebook6, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer1481111 = wx.BoxSizer( wx.VERTICAL )

        bSizer1651 = wx.BoxSizer( wx.HORIZONTAL )

        self.database_tablespace_panel = wx.Panel( self.m_panel801, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer13912 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText7012 = wx.StaticText( self.database_tablespace_panel, wx.ID_ANY, _(u"Tablespace"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText7012.Wrap( -1 )

        self.m_staticText7012.SetMinSize( wx.Size( 150,-1 ) )

        bSizer13912.Add( self.m_staticText7012, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        database_tablespaceChoices = []
        self.database_tablespace = wx.Choice( self.database_tablespace_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, database_tablespaceChoices, 0 )
        self.database_tablespace.SetSelection( 0 )
        bSizer13912.Add( self.database_tablespace, 1, wx.ALL, 5 )


        self.database_tablespace_panel.SetSizer( bSizer13912 )
        self.database_tablespace_panel.Layout()
        bSizer13912.Fit( self.database_tablespace_panel )
        bSizer1651.Add( self.database_tablespace_panel, 1, wx.ALIGN_CENTER, 5 )


        bSizer1481111.Add( bSizer1651, 0, wx.EXPAND, 5 )

        bSizer1662 = wx.BoxSizer( wx.HORIZONTAL )

        self.database_default_tablespace_panel = wx.Panel( self.m_panel801, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer1391212 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText701212 = wx.StaticText( self.database_default_tablespace_panel, wx.ID_ANY, _(u"Default tablespace"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText701212.Wrap( -1 )

        self.m_staticText701212.SetMinSize( wx.Size( 150,-1 ) )

        bSizer1391212.Add( self.m_staticText701212, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        database_default_tablespaceChoices = []
        self.database_default_tablespace = wx.Choice( self.database_default_tablespace_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, database_default_tablespaceChoices, 0 )
        self.database_default_tablespace.SetSelection( 0 )
        bSizer1391212.Add( self.database_default_tablespace, 1, wx.ALL, 5 )


        self.database_default_tablespace_panel.SetSizer( bSizer1391212 )
        self.database_default_tablespace_panel.Layout()
        bSizer1391212.Fit( self.database_default_tablespace_panel )
        bSizer1662.Add( self.database_default_tablespace_panel, 1, wx.ALIGN_CENTER, 5 )

        self.database_temporary_tablespace_panel = wx.Panel( self.m_panel801, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer13912121 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText7012121 = wx.StaticText( self.database_temporary_tablespace_panel, wx.ID_ANY, _(u"Temporary tablespace"), wx.DefaultPosition, wx.DefaultSize, wx.ST_ELLIPSIZE_END )
        self.m_staticText7012121.Wrap( -1 )

        self.m_staticText7012121.SetMinSize( wx.Size( 150,-1 ) )

        bSizer13912121.Add( self.m_staticText7012121, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        database_temporary_tablespaceChoices = []
        self.database_temporary_tablespace = wx.Choice( self.database_temporary_tablespace_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, database_temporary_tablespaceChoices, 0 )
        self.database_temporary_tablespace.SetSelection( 0 )
        bSizer13912121.Add( self.database_temporary_tablespace, 1, wx.ALL, 5 )


        self.database_temporary_tablespace_panel.SetSizer( bSizer13912121 )
        self.database_temporary_tablespace_panel.Layout()
        bSizer13912121.Fit( self.database_temporary_tablespace_panel )
        bSizer1662.Add( self.database_temporary_tablespace_panel, 1, wx.ALIGN_CENTER, 5 )


        bSizer1481111.Add( bSizer1662, 0, wx.EXPAND, 5 )

        bSizer167 = wx.BoxSizer( wx.HORIZONTAL )

        self.database_quota_panel = wx.Panel( self.m_panel801, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer1391211 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText701211 = wx.StaticText( self.database_quota_panel, wx.ID_ANY, _(u"Quota"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText701211.Wrap( -1 )

        self.m_staticText701211.SetMinSize( wx.Size( 150,-1 ) )

        bSizer1391211.Add( self.m_staticText701211, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.database_quota = wx.TextCtrl( self.database_quota_panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer1391211.Add( self.database_quota, 1, wx.ALL, 5 )


        self.database_quota_panel.SetSizer( bSizer1391211 )
        self.database_quota_panel.Layout()
        bSizer1391211.Fit( self.database_quota_panel )
        bSizer167.Add( self.database_quota_panel, 1, wx.ALIGN_CENTER, 5 )

        self.database_unlimited_quota_panel = wx.Panel( self.m_panel801, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer13911111 = wx.BoxSizer( wx.HORIZONTAL )

        self.database_unlimited_quota = wx.CheckBox( self.database_unlimited_quota_panel, wx.ID_ANY, _(u"Unlimited quota"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer13911111.Add( self.database_unlimited_quota, 0, wx.ALIGN_CENTER|wx.ALL, 5 )


        self.database_unlimited_quota_panel.SetSizer( bSizer13911111 )
        self.database_unlimited_quota_panel.Layout()
        bSizer13911111.Fit( self.database_unlimited_quota_panel )
        bSizer167.Add( self.database_unlimited_quota_panel, 1, wx.ALIGN_CENTER, 5 )


        bSizer1481111.Add( bSizer167, 0, wx.EXPAND, 5 )


        self.m_panel801.SetSizer( bSizer1481111 )
        self.m_panel801.Layout()
        bSizer1481111.Fit( self.m_panel801 )
        self.m_notebook6.AddPage( self.m_panel801, _(u"Advanced"), False )
        self.m_panel811 = wx.Panel( self.m_notebook6, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer163 = wx.BoxSizer( wx.VERTICAL )

        bSizer1481 = wx.BoxSizer( wx.HORIZONTAL )

        self.database_password_panel = wx.Panel( self.m_panel811, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer139121 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText70121 = wx.StaticText( self.database_password_panel, wx.ID_ANY, _(u"Password"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText70121.Wrap( -1 )

        self.m_staticText70121.SetMinSize( wx.Size( 150,-1 ) )

        bSizer139121.Add( self.m_staticText70121, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.m_textCtrl36 = wx.TextCtrl( self.database_password_panel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_PASSWORD )
        bSizer139121.Add( self.m_textCtrl36, 1, wx.ALL, 5 )


        self.database_password_panel.SetSizer( bSizer139121 )
        self.database_password_panel.Layout()
        bSizer139121.Fit( self.database_password_panel )
        bSizer1481.Add( self.database_password_panel, 1, wx.ALIGN_CENTER, 5 )

        self.database_password_expire_panel = wx.Panel( self.m_panel811, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer139111111 = wx.BoxSizer( wx.HORIZONTAL )

        self.database_password_expire = wx.CheckBox( self.database_password_expire_panel, wx.ID_ANY, _(u"Password expire"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer139111111.Add( self.database_password_expire, 0, wx.ALIGN_CENTER|wx.ALL, 5 )


        self.database_password_expire_panel.SetSizer( bSizer139111111 )
        self.database_password_expire_panel.Layout()
        bSizer139111111.Fit( self.database_password_expire_panel )
        bSizer1481.Add( self.database_password_expire_panel, 1, wx.ALIGN_CENTER, 5 )


        bSizer163.Add( bSizer1481, 0, wx.EXPAND, 5 )

        bSizer148111 = wx.BoxSizer( wx.HORIZONTAL )

        self.database_account_status_panel = wx.Panel( self.m_panel811, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer13912111 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText7012111 = wx.StaticText( self.database_account_status_panel, wx.ID_ANY, _(u"Account status"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText7012111.Wrap( -1 )

        self.m_staticText7012111.SetMinSize( wx.Size( 150,-1 ) )

        bSizer13912111.Add( self.m_staticText7012111, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        database_account_statusChoices = []
        self.database_account_status = wx.Choice( self.database_account_status_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, database_account_statusChoices, 0 )
        self.database_account_status.SetSelection( 0 )
        bSizer13912111.Add( self.database_account_status, 1, wx.ALL, 5 )


        self.database_account_status_panel.SetSizer( bSizer13912111 )
        self.database_account_status_panel.Layout()
        bSizer13912111.Fit( self.database_account_status_panel )
        bSizer148111.Add( self.database_account_status_panel, 1, wx.ALIGN_CENTER, 5 )

        self.database_profile_panel = wx.Panel( self.m_panel811, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer1391111 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText701111 = wx.StaticText( self.database_profile_panel, wx.ID_ANY, _(u"Profile"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText701111.Wrap( -1 )

        self.m_staticText701111.SetMinSize( wx.Size( 150,-1 ) )

        bSizer1391111.Add( self.m_staticText701111, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        database_profileChoices = []
        self.database_profile = wx.Choice( self.database_profile_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, database_profileChoices, 0 )
        self.database_profile.SetSelection( 0 )
        bSizer1391111.Add( self.database_profile, 1, wx.ALL, 5 )


        self.database_profile_panel.SetSizer( bSizer1391111 )
        self.database_profile_panel.Layout()
        bSizer1391111.Fit( self.database_profile_panel )
        bSizer148111.Add( self.database_profile_panel, 1, wx.ALIGN_CENTER, 5 )


        bSizer163.Add( bSizer148111, 0, wx.EXPAND, 5 )


        self.m_panel811.SetSizer( bSizer163 )
        self.m_panel811.Layout()
        bSizer163.Fit( self.m_panel811 )
        self.m_notebook6.AddPage( self.m_panel811, _(u"Security"), False )

        bSizer158.Add( self.m_notebook6, 1, wx.EXPAND | wx.ALL, 5 )


        self.m_panel54.SetSizer( bSizer158 )
        self.m_panel54.Layout()
        bSizer158.Fit( self.m_panel54 )
        self.m_panel651 = wx.Panel( self.m_splitter7, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer149 = wx.BoxSizer( wx.VERTICAL )

        self.m_notebook10 = wx.Notebook( self.m_panel651, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_panel55 = wx.Panel( self.m_notebook10, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer154 = wx.BoxSizer( wx.VERTICAL )

        self.m_toolBar51 = wx.ToolBar( self.m_panel55, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL|wx.TB_HORZ_TEXT )
        self.tool_insert_table = self.m_toolBar51.AddTool( wx.ID_ANY, _(u"Add new table"), wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Add new table"), _(u"Add new table"), None )

        self.tool_clone_table = self.m_toolBar51.AddTool( wx.ID_ANY, _(u"Clone table"), wx.Bitmap( u"icons/16x16/page_copy.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Clone table"), _(u"Clone table"), None )

        self.tool_delete_table = self.m_toolBar51.AddTool( wx.ID_ANY, _(u"Delete table"), wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Delete table"), _(u"Delete table"), None )

        self.m_toolBar51.Realize()

        bSizer154.Add( self.m_toolBar51, 0, wx.EXPAND, 5 )

        self.list_ctrl_database_tables = wx.dataview.DataViewCtrl( self.m_panel55, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_dataViewColumn12 = self.list_ctrl_database_tables.AppendTextColumn( _(u"Name"), 0, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        self.m_dataViewColumn13 = self.list_ctrl_database_tables.AppendTextColumn( _(u"Rows"), 1, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_RIGHT, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        self.m_dataViewColumn14 = self.list_ctrl_database_tables.AppendTextColumn( _(u"Size"), 2, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_RIGHT, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        self.m_dataViewColumn15 = self.list_ctrl_database_tables.AppendDateColumn( _(u"Created at"), 3, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        self.m_dataViewColumn16 = self.list_ctrl_database_tables.AppendDateColumn( _(u"Updated at"), 4, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        self.m_dataViewColumn17 = self.list_ctrl_database_tables.AppendTextColumn( _(u"Engine"), 5, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        self.m_dataViewColumn19 = self.list_ctrl_database_tables.AppendTextColumn( _(u"Collation"), 6, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        self.m_dataViewColumn18 = self.list_ctrl_database_tables.AppendTextColumn( _(u"Comments"), 7, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        bSizer154.Add( self.list_ctrl_database_tables, 1, wx.ALL|wx.EXPAND, 5 )


        self.m_panel55.SetSizer( bSizer154 )
        self.m_panel55.Layout()
        bSizer154.Fit( self.m_panel55 )
        self.m_notebook10.AddPage( self.m_panel55, _(u"Tables"), True )
        self.m_panel65 = wx.Panel( self.m_notebook10, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer1482 = wx.BoxSizer( wx.VERTICAL )

        self.m_toolBar5 = wx.ToolBar( self.m_panel65, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL|wx.TB_HORZ_TEXT )
        self.tool_insert_view = self.m_toolBar5.AddTool( wx.ID_ANY, _(u"Add new view"), wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Add new view"), _(u"Add new view"), None )

        self.tool_clone_view = self.m_toolBar5.AddTool( wx.ID_ANY, _(u"Clone view"), wx.Bitmap( u"icons/16x16/page_copy.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Clone view"), _(u"Clone view"), None )

        self.tool_delete_view = self.m_toolBar5.AddTool( wx.ID_ANY, _(u"Delete view"), wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Delete view"), _(u"Delete view"), None )

        self.m_toolBar5.Realize()

        bSizer1482.Add( self.m_toolBar5, 0, wx.EXPAND, 5 )

        self.list_ctrl_database_views = wx.dataview.DataViewCtrl( self.m_panel65, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_dataViewColumn121 = self.list_ctrl_database_views.AppendTextColumn( _(u"Name"), 0, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        self.m_dataViewColumn131 = self.list_ctrl_database_views.AppendTextColumn( _(u"Definition"), 1, wx.dataview.DATAVIEW_CELL_INERT, -1, 0, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        bSizer1482.Add( self.list_ctrl_database_views, 1, wx.ALL|wx.EXPAND, 5 )


        self.m_panel65.SetSizer( bSizer1482 )
        self.m_panel65.Layout()
        bSizer1482.Fit( self.m_panel65 )
        self.m_notebook10.AddPage( self.m_panel65, _(u"Views"), False )
        self.m_panel652 = wx.Panel( self.m_notebook10, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer14821 = wx.BoxSizer( wx.VERTICAL )

        self.m_toolBar52 = wx.ToolBar( self.m_panel652, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL|wx.TB_HORZ_TEXT )
        self.tool_insert_procedure = self.m_toolBar52.AddTool( wx.ID_ANY, _(u"Add new procedure"), wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Add new procedure"), _(u"Add new procedure"), None )

        self.tool_clone_procedure = self.m_toolBar52.AddTool( wx.ID_ANY, _(u"Clone procedure"), wx.Bitmap( u"icons/16x16/page_copy.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Clone procedure"), _(u"Clone procedure"), None )

        self.tool_delete_procedure = self.m_toolBar52.AddTool( wx.ID_ANY, _(u"Delete procedure"), wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Delete procedure"), _(u"Delete procedure"), None )

        self.m_toolBar52.Realize()

        bSizer14821.Add( self.m_toolBar52, 0, wx.EXPAND, 5 )

        self.list_ctrl_database_procedure = wx.dataview.DataViewCtrl( self.m_panel652, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_dataViewColumn1211 = self.list_ctrl_database_procedure.AppendTextColumn( _(u"Name"), 0, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        self.m_dataViewColumn1311 = self.list_ctrl_database_procedure.AppendTextColumn( _(u"Definition"), 1, wx.dataview.DATAVIEW_CELL_INERT, -1, 0, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        bSizer14821.Add( self.list_ctrl_database_procedure, 1, wx.ALL|wx.EXPAND, 5 )


        self.m_panel652.SetSizer( bSizer14821 )
        self.m_panel652.Layout()
        bSizer14821.Fit( self.m_panel652 )
        self.m_notebook10.AddPage( self.m_panel652, _(u"Procedures"), False )
        self.m_panel6521 = wx.Panel( self.m_notebook10, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer148211 = wx.BoxSizer( wx.VERTICAL )

        self.m_toolBar521 = wx.ToolBar( self.m_panel6521, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL|wx.TB_HORZ_TEXT )
        self.tool_insert_function = self.m_toolBar521.AddTool( wx.ID_ANY, _(u"Add new function"), wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Add new function"), _(u"Add new function"), None )

        self.tool_clone_function = self.m_toolBar521.AddTool( wx.ID_ANY, _(u"Clone function"), wx.Bitmap( u"icons/16x16/page_copy.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Clone function"), _(u"Clone function"), None )

        self.tool_delete_function = self.m_toolBar521.AddTool( wx.ID_ANY, _(u"Delete function"), wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Delete function"), _(u"Delete function"), None )

        self.m_toolBar521.Realize()

        bSizer148211.Add( self.m_toolBar521, 0, wx.EXPAND, 5 )

        self.list_ctrl_database_function = wx.dataview.DataViewCtrl( self.m_panel6521, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_dataViewColumn12111 = self.list_ctrl_database_function.AppendTextColumn( _(u"Name"), 0, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        self.m_dataViewColumn13111 = self.list_ctrl_database_function.AppendTextColumn( _(u"Definition"), 1, wx.dataview.DATAVIEW_CELL_INERT, -1, 0, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        bSizer148211.Add( self.list_ctrl_database_function, 1, wx.ALL|wx.EXPAND, 5 )


        self.m_panel6521.SetSizer( bSizer148211 )
        self.m_panel6521.Layout()
        bSizer148211.Fit( self.m_panel6521 )
        self.m_notebook10.AddPage( self.m_panel6521, _(u"Functions"), False )
        self.m_panel65211 = wx.Panel( self.m_notebook10, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer1482111 = wx.BoxSizer( wx.VERTICAL )

        self.m_toolBar5211 = wx.ToolBar( self.m_panel65211, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL|wx.TB_HORZ_TEXT )
        self.tool_insert_trigger = self.m_toolBar5211.AddTool( wx.ID_ANY, _(u"Add new trigger"), wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Add new trigger"), _(u"Add new trigger"), None )

        self.tool_clone_trigger = self.m_toolBar5211.AddTool( wx.ID_ANY, _(u"Clone trigger"), wx.Bitmap( u"icons/16x16/page_copy.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Clone trigger"), _(u"Clone trigger"), None )

        self.tool_delete_trigger = self.m_toolBar5211.AddTool( wx.ID_ANY, _(u"Delete trigger"), wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Delete trigger"), _(u"Delete trigger"), None )

        self.m_toolBar5211.Realize()

        bSizer1482111.Add( self.m_toolBar5211, 0, wx.EXPAND, 5 )

        self.list_ctrl_database_trigger = wx.dataview.DataViewCtrl( self.m_panel65211, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_dataViewColumn121111 = self.list_ctrl_database_trigger.AppendTextColumn( _(u"Name"), 0, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        self.m_dataViewColumn131111 = self.list_ctrl_database_trigger.AppendTextColumn( _(u"Definition"), 1, wx.dataview.DATAVIEW_CELL_INERT, -1, 0, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        bSizer1482111.Add( self.list_ctrl_database_trigger, 1, wx.ALL|wx.EXPAND, 5 )


        self.m_panel65211.SetSizer( bSizer1482111 )
        self.m_panel65211.Layout()
        bSizer1482111.Fit( self.m_panel65211 )
        self.m_notebook10.AddPage( self.m_panel65211, _(u"Triggers"), False )
        self.m_panel652111 = wx.Panel( self.m_notebook10, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer14821111 = wx.BoxSizer( wx.VERTICAL )

        self.m_toolBar52111 = wx.ToolBar( self.m_panel652111, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL|wx.TB_HORZ_TEXT )
        self.tool_insert_event = self.m_toolBar52111.AddTool( wx.ID_ANY, _(u"Add new event"), wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Add new event"), _(u"Add new event"), None )

        self.tool_clone_event = self.m_toolBar52111.AddTool( wx.ID_ANY, _(u"Clone event"), wx.Bitmap( u"icons/16x16/page_copy.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Clone event"), _(u"Clone event"), None )

        self.tool_delete_event = self.m_toolBar52111.AddTool( wx.ID_ANY, _(u"Delete event"), wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Delete event"), _(u"Delete event"), None )

        self.m_toolBar52111.Realize()

        bSizer14821111.Add( self.m_toolBar52111, 0, wx.EXPAND, 5 )

        self.list_ctrl_database_event = wx.dataview.DataViewCtrl( self.m_panel652111, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_dataViewColumn1211111 = self.list_ctrl_database_event.AppendTextColumn( _(u"Name"), 0, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        self.m_dataViewColumn1311111 = self.list_ctrl_database_event.AppendTextColumn( _(u"Definition"), 1, wx.dataview.DATAVIEW_CELL_INERT, -1, 0, wx.dataview.DATAVIEW_COL_RESIZABLE|wx.dataview.DATAVIEW_COL_SORTABLE )
        bSizer14821111.Add( self.list_ctrl_database_event, 1, wx.ALL|wx.EXPAND, 5 )


        self.m_panel652111.SetSizer( bSizer14821111 )
        self.m_panel652111.Layout()
        bSizer14821111.Fit( self.m_panel652111 )
        self.m_notebook10.AddPage( self.m_panel652111, _(u"Events"), False )

        bSizer149.Add( self.m_notebook10, 1, wx.EXPAND | wx.ALL, 5 )


        self.m_panel651.SetSizer( bSizer149 )
        self.m_panel651.Layout()
        bSizer149.Fit( self.m_panel651 )
        self.m_splitter7.SplitHorizontally( self.m_panel54, self.m_panel651, 200 )
        bSizer27.Add( self.m_splitter7, 1, wx.EXPAND, 5 )

        bSizer80 = wx.BoxSizer( wx.VERTICAL )

        bSizer138 = wx.BoxSizer( wx.HORIZONTAL )

        self.btn_cancel_database = wx.Button( self.panel_database, wx.ID_ANY, _(u"Cancel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_cancel_database.Enable( False )

        bSizer138.Add( self.btn_cancel_database, 0, wx.ALL, 5 )

        self.btn_delete_database = wx.Button( self.panel_database, wx.ID_ANY, _(u"Delete"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_delete_database.Enable( False )

        bSizer138.Add( self.btn_delete_database, 0, wx.ALL, 5 )

        self.btn_apply_database = wx.Button( self.panel_database, wx.ID_ANY, _(u"Apply"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_apply_database.Enable( False )

        bSizer138.Add( self.btn_apply_database, 0, wx.ALL, 5 )


        bSizer80.Add( bSizer138, 0, wx.EXPAND, 5 )


        bSizer27.Add( bSizer80, 0, wx.EXPAND, 5 )


        self.panel_database.SetSizer( bSizer27 )
        self.panel_database.Layout()
        bSizer27.Fit( self.panel_database )
        self.MainFrameNotebook.AddPage( self.panel_database, _(u"Database"), True )
        MainFrameNotebookBitmap = wx.Bitmap( u"icons/16x16/database.png", wx.BITMAP_TYPE_ANY )
        if ( MainFrameNotebookBitmap.IsOk() ):
            MainFrameNotebookImages.Add( MainFrameNotebookBitmap )
            self.MainFrameNotebook.SetPageImage( MainFrameNotebookIndex, MainFrameNotebookIndex )
            MainFrameNotebookIndex += 1

        self.panel_table = wx.Panel( self.MainFrameNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer251 = wx.BoxSizer( wx.VERTICAL )

        self.m_splitter41 = wx.SplitterWindow( self.panel_table, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_LIVE_UPDATE )
        self.m_splitter41.SetSashGravity( 0.5 )
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

        table_engineChoices = []
        self.table_engine = wx.Choice( self.PanelTableOptions, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, table_engineChoices, 0 )
        self.table_engine.SetSelection( 0 )
        bSizer2712.Add( self.table_engine, 1, wx.ALL|wx.EXPAND, 5 )


        gSizer11.Add( bSizer2712, 0, wx.EXPAND, 5 )

        bSizer2721 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText821 = wx.StaticText( self.PanelTableOptions, wx.ID_ANY, _(u"Default Collation"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText821.Wrap( -1 )

        bSizer2721.Add( self.m_staticText821, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        table_collationChoices = []
        self.table_collation = wx.Choice( self.PanelTableOptions, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, table_collationChoices, 0 )
        self.table_collation.SetSelection( 0 )
        bSizer2721.Add( self.table_collation, 1, wx.ALL, 5 )

        self.convert_data_collation = wx.CheckBox( self.PanelTableOptions, wx.ID_ANY, _(u"Convert data"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer2721.Add( self.convert_data_collation, 0, wx.ALIGN_CENTER|wx.ALL, 5 )


        gSizer11.Add( bSizer2721, 0, wx.EXPAND, 5 )

        bSizer145 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText71 = wx.StaticText( self.PanelTableOptions, wx.ID_ANY, _(u"Row format"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText71.Wrap( -1 )

        self.m_staticText71.SetMinSize( wx.Size( 150,-1 ) )

        bSizer145.Add( self.m_staticText71, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        table_row_formatChoices = []
        self.table_row_format = wx.Choice( self.PanelTableOptions, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, table_row_formatChoices, 0 )
        self.table_row_format.SetSelection( 0 )
        bSizer145.Add( self.table_row_format, 1, wx.ALL, 5 )


        gSizer11.Add( bSizer145, 1, wx.EXPAND, 5 )


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

        self.m_toolBar12 = wx.ToolBar( self.PanelTableIndex, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORZ_TEXT|wx.TB_TEXT|wx.TB_VERTICAL )
        self.m_tool43 = self.m_toolBar12.AddTool( wx.ID_ANY, _(u"Remove"), wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_tool44 = self.m_toolBar12.AddTool( wx.ID_ANY, _(u"Clear"), wx.Bitmap( u"icons/16x16/cross.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_toolBar12.Realize()

        bSizer28.Add( self.m_toolBar12, 0, wx.EXPAND, 5 )

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
        bSizer77 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_toolBar121 = wx.ToolBar( self.PanelTableFK, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORZ_TEXT|wx.TB_TEXT|wx.TB_VERTICAL )
        self.m_tool49 = self.m_toolBar121.AddTool( wx.ID_ANY, _(u"Insert"), wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_tool431 = self.m_toolBar121.AddTool( wx.ID_ANY, _(u"Remove"), wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_tool441 = self.m_toolBar121.AddTool( wx.ID_ANY, _(u"Clear"), wx.Bitmap( u"icons/16x16/cross.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_toolBar121.Realize()

        bSizer77.Add( self.m_toolBar121, 0, wx.EXPAND, 5 )

        self.dv_table_foreign_keys = TableForeignKeysDataViewCtrl( self.PanelTableFK, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer77.Add( self.dv_table_foreign_keys, 1, wx.ALL|wx.EXPAND, 0 )


        self.PanelTableFK.SetSizer( bSizer77 )
        self.PanelTableFK.Layout()
        bSizer77.Fit( self.PanelTableFK )
        self.m_notebook3.AddPage( self.PanelTableFK, _(u"Foreign Keys"), False )
        m_notebook3Bitmap = wx.Bitmap( u"icons/16x16/table_relationship.png", wx.BITMAP_TYPE_ANY )
        if ( m_notebook3Bitmap.IsOk() ):
            m_notebook3Images.Add( m_notebook3Bitmap )
            self.m_notebook3.SetPageImage( m_notebook3Index, m_notebook3Index )
            m_notebook3Index += 1

        self.PanelTableCheck = wx.Panel( self.m_notebook3, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer771 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_toolBar1211 = wx.ToolBar( self.PanelTableCheck, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORZ_TEXT|wx.TB_TEXT|wx.TB_VERTICAL )
        self.m_tool491 = self.m_toolBar1211.AddTool( wx.ID_ANY, _(u"Insert"), wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_tool4311 = self.m_toolBar1211.AddTool( wx.ID_ANY, _(u"Remove"), wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_tool4411 = self.m_toolBar1211.AddTool( wx.ID_ANY, _(u"Clear"), wx.Bitmap( u"icons/16x16/cross.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_toolBar1211.Realize()

        bSizer771.Add( self.m_toolBar1211, 0, wx.EXPAND, 5 )

        self.dv_table_checks = TableCheckDataViewCtrl( self.PanelTableCheck, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer771.Add( self.dv_table_checks, 1, wx.ALL|wx.EXPAND, 0 )


        self.PanelTableCheck.SetSizer( bSizer771 )
        self.PanelTableCheck.Layout()
        bSizer771.Fit( self.PanelTableCheck )
        self.m_notebook3.AddPage( self.PanelTableCheck, _(u"Checks"), False )
        m_notebook3Bitmap = wx.Bitmap( u"icons/16x16/tick.png", wx.BITMAP_TYPE_ANY )
        if ( m_notebook3Bitmap.IsOk() ):
            m_notebook3Images.Add( m_notebook3Bitmap )
            self.m_notebook3.SetPageImage( m_notebook3Index, m_notebook3Index )
            m_notebook3Index += 1

        self.PanelTableCreate = wx.Panel( self.m_notebook3, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer109 = wx.BoxSizer( wx.VERTICAL )

        self.sql_create_table = wx.stc.StyledTextCtrl( self.PanelTableCreate, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,200 ), 0)
        self.sql_create_table.SetUseTabs ( True )
        self.sql_create_table.SetTabWidth ( 4 )
        self.sql_create_table.SetIndent ( 4 )
        self.sql_create_table.SetTabIndents( True )
        self.sql_create_table.SetBackSpaceUnIndents( True )
        self.sql_create_table.SetViewEOL( False )
        self.sql_create_table.SetViewWhiteSpace( False )
        self.sql_create_table.SetMarginWidth( 2, 0 )
        self.sql_create_table.SetIndentationGuides( True )
        self.sql_create_table.SetReadOnly( False )
        self.sql_create_table.SetMarginWidth( 1, 0 )
        self.sql_create_table.SetMarginType( 0, wx.stc.STC_MARGIN_NUMBER )
        self.sql_create_table.SetMarginWidth( 0, self.sql_create_table.TextWidth( wx.stc.STC_STYLE_LINENUMBER, "_99999" ) )
        self.sql_create_table.MarkerDefine( wx.stc.STC_MARKNUM_FOLDER, wx.stc.STC_MARK_BOXPLUS )
        self.sql_create_table.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDER, wx.BLACK)
        self.sql_create_table.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDER, wx.WHITE)
        self.sql_create_table.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.stc.STC_MARK_BOXMINUS )
        self.sql_create_table.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.BLACK )
        self.sql_create_table.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.WHITE )
        self.sql_create_table.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERSUB, wx.stc.STC_MARK_EMPTY )
        self.sql_create_table.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEREND, wx.stc.STC_MARK_BOXPLUS )
        self.sql_create_table.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEREND, wx.BLACK )
        self.sql_create_table.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEREND, wx.WHITE )
        self.sql_create_table.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.stc.STC_MARK_BOXMINUS )
        self.sql_create_table.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.BLACK)
        self.sql_create_table.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.WHITE)
        self.sql_create_table.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERMIDTAIL, wx.stc.STC_MARK_EMPTY )
        self.sql_create_table.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERTAIL, wx.stc.STC_MARK_EMPTY )
        self.sql_create_table.SetSelBackground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT ) )
        self.sql_create_table.SetSelForeground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT ) )
        bSizer109.Add( self.sql_create_table, 1, wx.EXPAND | wx.ALL, 5 )


        self.PanelTableCreate.SetSizer( bSizer109 )
        self.PanelTableCreate.Layout()
        bSizer109.Fit( self.PanelTableCreate )
        self.m_notebook3.AddPage( self.PanelTableCreate, _(u"Create"), False )
        m_notebook3Bitmap = wx.Bitmap( u"icons/16x16/code-folding.png", wx.BITMAP_TYPE_ANY )
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

        self.toolbar_columns = wx.ToolBar( self.panel_table_columns, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL|wx.TB_HORZ_TEXT )
        self.m_staticText39 = wx.StaticText( self.toolbar_columns, wx.ID_ANY, _(u"Columns:"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText39.Wrap( -1 )

        self.toolbar_columns.AddControl( self.m_staticText39 )
        self.tool_add_column = self.toolbar_columns.AddTool( wx.ID_ANY, _(u"Add"), wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.tool_remove_column = self.toolbar_columns.AddTool( wx.ID_ANY, _(u"Remove"), wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.toolbar_columns.AddSeparator()

        self.tool_move_up_column = self.toolbar_columns.AddTool( wx.ID_ANY, _(u"Move Up"), wx.Bitmap( u"icons/16x16/arrow_up.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.tool_move_down_column = self.toolbar_columns.AddTool( wx.ID_ANY, _(u"Move Down"), wx.Bitmap( u"icons/16x16/arrow_down.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.toolbar_columns.Realize()

        bSizer54.Add( self.toolbar_columns, 0, wx.EXPAND, 5 )

        self.list_ctrl_table_columns = TableColumnsDataViewCtrl( self.panel_table_columns, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer54.Add( self.list_ctrl_table_columns, 1, wx.ALL|wx.EXPAND, 5 )

        bSizer52 = wx.BoxSizer( wx.HORIZONTAL )

        self.btn_delete_table = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Delete"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer52.Add( self.btn_delete_table, 0, wx.ALL, 5 )

        self.btn_cancel_table = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Cancel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_cancel_table.Enable( False )

        bSizer52.Add( self.btn_cancel_table, 0, wx.ALL, 5 )

        self.btn_apply_table = wx.Button( self.panel_table_columns, wx.ID_ANY, _(u"Apply"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_apply_table.Enable( False )

        bSizer52.Add( self.btn_apply_table, 0, wx.ALL, 5 )


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
        self.MainFrameNotebook.AddPage( self.panel_table, _(u"Table"), False )
        MainFrameNotebookBitmap = wx.Bitmap( u"icons/16x16/table.png", wx.BITMAP_TYPE_ANY )
        if ( MainFrameNotebookBitmap.IsOk() ):
            MainFrameNotebookImages.Add( MainFrameNotebookBitmap )
            self.MainFrameNotebook.SetPageImage( MainFrameNotebookIndex, MainFrameNotebookIndex )
            MainFrameNotebookIndex += 1

        self.panel_views = wx.Panel( self.MainFrameNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer84 = wx.BoxSizer( wx.VERTICAL )

        self.m_splitter11 = wx.SplitterWindow( self.panel_views, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_3D )
        self.m_splitter11.Bind( wx.EVT_IDLE, self.m_splitter11OnIdle )

        self.m_panel79 = wx.Panel( self.m_splitter11, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer170 = wx.BoxSizer( wx.VERTICAL )

        self.m_notebook7 = wx.Notebook( self.m_panel79, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.pnl_view_editor_root = wx.Panel( self.m_notebook7, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer85 = wx.BoxSizer( wx.VERTICAL )

        bSizer87 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText40 = wx.StaticText( self.pnl_view_editor_root, wx.ID_ANY, _(u"Name"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText40.Wrap( -1 )

        self.m_staticText40.SetMinSize( wx.Size( 150,-1 ) )

        bSizer87.Add( self.m_staticText40, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.txt_view_name = wx.TextCtrl( self.pnl_view_editor_root, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer87.Add( self.txt_view_name, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        bSizer85.Add( bSizer87, 0, wx.ALL|wx.EXPAND, 5 )

        bSizer89 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer116 = wx.BoxSizer( wx.VERTICAL )

        self.pnl_row_schema = wx.Panel( self.pnl_view_editor_root, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        szr_view_schema = wx.BoxSizer( wx.HORIZONTAL )

        self.lbl_view_schema = wx.StaticText( self.pnl_row_schema, wx.ID_ANY, _(u"Schema"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lbl_view_schema.Wrap( -1 )

        self.lbl_view_schema.SetMinSize( wx.Size( 150,-1 ) )

        szr_view_schema.Add( self.lbl_view_schema, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        cho_view_schemaChoices = []
        self.cho_view_schema = wx.Choice( self.pnl_row_schema, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, cho_view_schemaChoices, 0 )
        self.cho_view_schema.SetSelection( 0 )
        szr_view_schema.Add( self.cho_view_schema, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        self.pnl_row_schema.SetSizer( szr_view_schema )
        self.pnl_row_schema.Layout()
        szr_view_schema.Fit( self.pnl_row_schema )
        bSizer116.Add( self.pnl_row_schema, 0, wx.EXPAND | wx.ALL, 5 )


        bSizer89.Add( bSizer116, 1, wx.EXPAND, 5 )


        bSizer85.Add( bSizer89, 0, wx.EXPAND, 5 )


        self.pnl_view_editor_root.SetSizer( bSizer85 )
        self.pnl_view_editor_root.Layout()
        bSizer85.Fit( self.pnl_view_editor_root )
        self.m_notebook7.AddPage( self.pnl_view_editor_root, _(u"General"), False )
        self.m_panel76 = wx.Panel( self.m_notebook7, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer1661 = wx.BoxSizer( wx.VERTICAL )

        self.pnl_row_algorithm = wx.Panel( self.m_panel76, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        szr_view_algorithm = wx.StaticBoxSizer( wx.HORIZONTAL, self.pnl_row_algorithm, _(u"Algorithm") )

        self.rad_view_algorithm_undefined = wx.RadioButton( szr_view_algorithm.GetStaticBox(), wx.ID_ANY, _(u"UNDEFINED"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        szr_view_algorithm.Add( self.rad_view_algorithm_undefined, 0, wx.ALL, 5 )

        self.rad_view_algorithm_merge = wx.RadioButton( szr_view_algorithm.GetStaticBox(), wx.ID_ANY, _(u"MERGE"), wx.DefaultPosition, wx.DefaultSize, 0 )
        szr_view_algorithm.Add( self.rad_view_algorithm_merge, 0, wx.ALL, 5 )

        self.rad_view_algorithm_temptable = wx.RadioButton( szr_view_algorithm.GetStaticBox(), wx.ID_ANY, _(u"TEMPTABLE"), wx.DefaultPosition, wx.DefaultSize, 0 )
        szr_view_algorithm.Add( self.rad_view_algorithm_temptable, 0, wx.ALL, 5 )


        self.pnl_row_algorithm.SetSizer( szr_view_algorithm )
        self.pnl_row_algorithm.Layout()
        szr_view_algorithm.Fit( self.pnl_row_algorithm )
        bSizer1661.Add( self.pnl_row_algorithm, 0, wx.ALL|wx.EXPAND, 5 )

        self.pnl_row_constraint = wx.Panel( self.m_panel76, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        szr_view_constraint = wx.StaticBoxSizer( wx.VERTICAL, self.pnl_row_constraint, _(u"View constraint") )

        self.rad_view_constraint_none = wx.RadioButton( szr_view_constraint.GetStaticBox(), wx.ID_ANY, _(u"None"), wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        szr_view_constraint.Add( self.rad_view_constraint_none, 0, wx.ALL, 5 )

        self.rad_view_constraint_local = wx.RadioButton( szr_view_constraint.GetStaticBox(), wx.ID_ANY, _(u"LOCAL"), wx.DefaultPosition, wx.DefaultSize, 0 )
        szr_view_constraint.Add( self.rad_view_constraint_local, 0, wx.ALL, 5 )

        self.rad_view_constraint_cascaded = wx.RadioButton( szr_view_constraint.GetStaticBox(), wx.ID_ANY, _(u"CASCADE"), wx.DefaultPosition, wx.DefaultSize, 0 )
        szr_view_constraint.Add( self.rad_view_constraint_cascaded, 0, wx.ALL, 5 )

        self.rad_view_constraint_check_only = wx.RadioButton( szr_view_constraint.GetStaticBox(), wx.ID_ANY, _(u"CHECK ONLY"), wx.DefaultPosition, wx.DefaultSize, 0 )
        szr_view_constraint.Add( self.rad_view_constraint_check_only, 0, wx.ALL, 5 )

        self.rad_view_constraint_read_only = wx.RadioButton( szr_view_constraint.GetStaticBox(), wx.ID_ANY, _(u"READ ONLY"), wx.DefaultPosition, wx.DefaultSize, 0 )
        szr_view_constraint.Add( self.rad_view_constraint_read_only, 0, wx.ALL, 5 )


        self.pnl_row_constraint.SetSizer( szr_view_constraint )
        self.pnl_row_constraint.Layout()
        szr_view_constraint.Fit( self.pnl_row_constraint )
        bSizer1661.Add( self.pnl_row_constraint, 0, wx.ALL|wx.EXPAND, 5 )


        self.m_panel76.SetSizer( bSizer1661 )
        self.m_panel76.Layout()
        bSizer1661.Fit( self.m_panel76 )
        self.m_notebook7.AddPage( self.m_panel76, _(u"Behavior"), False )
        self.m_panel75 = wx.Panel( self.m_notebook7, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer165 = wx.BoxSizer( wx.VERTICAL )

        self.pnl_row_definer = wx.Panel( self.m_panel75, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        szr_view_definer = wx.BoxSizer( wx.HORIZONTAL )

        self.lbl_view_definer = wx.StaticText( self.pnl_row_definer, wx.ID_ANY, _(u"Definer"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lbl_view_definer.Wrap( -1 )

        self.lbl_view_definer.SetMinSize( wx.Size( 150,-1 ) )

        szr_view_definer.Add( self.lbl_view_definer, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        cmb_view_definerChoices = []
        self.cmb_view_definer = wx.ComboBox( self.pnl_row_definer, wx.ID_ANY, _(u"*"), wx.DefaultPosition, wx.DefaultSize, cmb_view_definerChoices, 0 )
        szr_view_definer.Add( self.cmb_view_definer, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        self.pnl_row_definer.SetSizer( szr_view_definer )
        self.pnl_row_definer.Layout()
        szr_view_definer.Fit( self.pnl_row_definer )
        bSizer165.Add( self.pnl_row_definer, 0, wx.EXPAND | wx.ALL, 5 )

        self.pnl_row_sql_security = wx.Panel( self.m_panel75, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        szr_view_sql_security = wx.BoxSizer( wx.HORIZONTAL )

        self.lbl_view_sql_security = wx.StaticText( self.pnl_row_sql_security, wx.ID_ANY, _(u"SQL security"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lbl_view_sql_security.Wrap( -1 )

        self.lbl_view_sql_security.SetMinSize( wx.Size( 150,-1 ) )

        szr_view_sql_security.Add( self.lbl_view_sql_security, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        cho_view_sql_securityChoices = [ _(u"DEFINER"), _(u"INVOKER") ]
        self.cho_view_sql_security = wx.Choice( self.pnl_row_sql_security, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, cho_view_sql_securityChoices, 0 )
        self.cho_view_sql_security.SetSelection( 0 )
        szr_view_sql_security.Add( self.cho_view_sql_security, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        self.pnl_row_sql_security.SetSizer( szr_view_sql_security )
        self.pnl_row_sql_security.Layout()
        szr_view_sql_security.Fit( self.pnl_row_sql_security )
        bSizer165.Add( self.pnl_row_sql_security, 0, wx.EXPAND | wx.ALL, 5 )

        self.pnl_row_security_barrier = wx.Panel( self.m_panel75, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer126 = wx.BoxSizer( wx.VERTICAL )

        self.chk_view_force = wx.CheckBox( self.pnl_row_security_barrier, wx.ID_ANY, _(u"Force"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer126.Add( self.chk_view_force, 0, wx.ALL, 5 )


        self.pnl_row_security_barrier.SetSizer( bSizer126 )
        self.pnl_row_security_barrier.Layout()
        bSizer126.Fit( self.pnl_row_security_barrier )
        bSizer165.Add( self.pnl_row_security_barrier, 0, wx.EXPAND, 5 )

        self.pnl_row_force = wx.Panel( self.m_panel75, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer127 = wx.BoxSizer( wx.VERTICAL )

        self.chk_view_security_barrier = wx.CheckBox( self.pnl_row_force, wx.ID_ANY, _(u"Security barrier"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer127.Add( self.chk_view_security_barrier, 0, wx.ALL, 5 )


        self.pnl_row_force.SetSizer( bSizer127 )
        self.pnl_row_force.Layout()
        bSizer127.Fit( self.pnl_row_force )
        bSizer165.Add( self.pnl_row_force, 0, wx.EXPAND, 5 )


        self.m_panel75.SetSizer( bSizer165 )
        self.m_panel75.Layout()
        bSizer165.Fit( self.m_panel75 )
        self.m_notebook7.AddPage( self.m_panel75, _(u"Security"), True )

        bSizer170.Add( self.m_notebook7, 0, wx.EXPAND | wx.ALL, 5 )


        self.m_panel79.SetSizer( bSizer170 )
        self.m_panel79.Layout()
        bSizer170.Fit( self.m_panel79 )
        self.m_panel80 = wx.Panel( self.m_splitter11, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer168 = wx.BoxSizer( wx.VERTICAL )

        self.stc_view_select = wx.stc.StyledTextCtrl( self.m_panel80, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,-1 ), 0)
        self.stc_view_select.SetUseTabs ( True )
        self.stc_view_select.SetTabWidth ( 4 )
        self.stc_view_select.SetIndent ( 4 )
        self.stc_view_select.SetTabIndents( True )
        self.stc_view_select.SetBackSpaceUnIndents( True )
        self.stc_view_select.SetViewEOL( False )
        self.stc_view_select.SetViewWhiteSpace( False )
        self.stc_view_select.SetMarginWidth( 2, 0 )
        self.stc_view_select.SetIndentationGuides( True )
        self.stc_view_select.SetReadOnly( False )
        self.stc_view_select.SetMarginWidth( 1, 0 )
        self.stc_view_select.SetMarginType( 0, wx.stc.STC_MARGIN_NUMBER )
        self.stc_view_select.SetMarginWidth( 0, self.stc_view_select.TextWidth( wx.stc.STC_STYLE_LINENUMBER, "_99999" ) )
        self.stc_view_select.MarkerDefine( wx.stc.STC_MARKNUM_FOLDER, wx.stc.STC_MARK_BOXPLUS )
        self.stc_view_select.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDER, wx.BLACK)
        self.stc_view_select.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDER, wx.WHITE)
        self.stc_view_select.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.stc.STC_MARK_BOXMINUS )
        self.stc_view_select.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.BLACK )
        self.stc_view_select.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.WHITE )
        self.stc_view_select.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERSUB, wx.stc.STC_MARK_EMPTY )
        self.stc_view_select.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEREND, wx.stc.STC_MARK_BOXPLUS )
        self.stc_view_select.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEREND, wx.BLACK )
        self.stc_view_select.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEREND, wx.WHITE )
        self.stc_view_select.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.stc.STC_MARK_BOXMINUS )
        self.stc_view_select.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.BLACK)
        self.stc_view_select.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.WHITE)
        self.stc_view_select.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERMIDTAIL, wx.stc.STC_MARK_EMPTY )
        self.stc_view_select.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERTAIL, wx.stc.STC_MARK_EMPTY )
        self.stc_view_select.SetSelBackground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT ) )
        self.stc_view_select.SetSelForeground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT ) )
        self.stc_view_select.SetMinSize( wx.Size( -1,200 ) )

        bSizer168.Add( self.stc_view_select, 1, wx.EXPAND | wx.ALL, 5 )


        self.m_panel80.SetSizer( bSizer168 )
        self.m_panel80.Layout()
        bSizer168.Fit( self.m_panel80 )
        self.m_splitter11.SplitHorizontally( self.m_panel79, self.m_panel80, 0 )
        bSizer84.Add( self.m_splitter11, 1, wx.EXPAND, 5 )

        bSizer91 = wx.BoxSizer( wx.HORIZONTAL )

        self.btn_delete_view = wx.Button( self.panel_views, wx.ID_ANY, _(u"Delete"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_delete_view.Enable( False )

        bSizer91.Add( self.btn_delete_view, 0, wx.ALL, 5 )

        self.btn_cancel_view = wx.Button( self.panel_views, wx.ID_ANY, _(u"Cancel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_cancel_view.Enable( False )

        bSizer91.Add( self.btn_cancel_view, 0, wx.ALL, 5 )

        self.btn_save_view = wx.Button( self.panel_views, wx.ID_ANY, _(u"Save"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_save_view.Enable( False )

        bSizer91.Add( self.btn_save_view, 0, wx.ALL, 5 )


        bSizer84.Add( bSizer91, 0, wx.EXPAND, 5 )


        self.panel_views.SetSizer( bSizer84 )
        self.panel_views.Layout()
        bSizer84.Fit( self.panel_views )
        self.MainFrameNotebook.AddPage( self.panel_views, _(u"View"), False )
        MainFrameNotebookBitmap = wx.Bitmap( u"icons/16x16/view.png", wx.BITMAP_TYPE_ANY )
        if ( MainFrameNotebookBitmap.IsOk() ):
            MainFrameNotebookImages.Add( MainFrameNotebookBitmap )
            self.MainFrameNotebook.SetPageImage( MainFrameNotebookIndex, MainFrameNotebookIndex )
            MainFrameNotebookIndex += 1

        self.panel_routine = wx.Panel( self.MainFrameNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer160 = wx.BoxSizer( wx.VERTICAL )

        self.m_splitter9 = wx.SplitterWindow( self.panel_routine, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_3D )
        self.m_splitter9.SetSashGravity( 0 )
        self.m_splitter9.Bind( wx.EVT_IDLE, self.m_splitter9OnIdle )

        self.m_panel73 = wx.Panel( self.m_splitter9, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer166 = wx.BoxSizer( wx.VERTICAL )

        self.m_notebook11 = wx.Notebook( self.m_panel73, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_panel81 = wx.Panel( self.m_notebook11, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer1701 = wx.BoxSizer( wx.VERTICAL )

        bSizer871 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText401 = wx.StaticText( self.m_panel81, wx.ID_ANY, _(u"Name"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText401.Wrap( -1 )

        self.m_staticText401.SetMinSize( wx.Size( 150,-1 ) )

        bSizer871.Add( self.m_staticText401, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.routine_name = wx.TextCtrl( self.m_panel81, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer871.Add( self.routine_name, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        bSizer1701.Add( bSizer871, 0, wx.EXPAND, 5 )

        szr_view_schema1 = wx.BoxSizer( wx.HORIZONTAL )

        self.lbl_view_schema1 = wx.StaticText( self.m_panel81, wx.ID_ANY, _(u"Schema"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lbl_view_schema1.Wrap( -1 )

        self.lbl_view_schema1.SetMinSize( wx.Size( 150,-1 ) )

        szr_view_schema1.Add( self.lbl_view_schema1, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        routine_schemaChoices = []
        self.routine_schema = wx.Choice( self.m_panel81, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, routine_schemaChoices, 0 )
        self.routine_schema.SetSelection( 0 )
        szr_view_schema1.Add( self.routine_schema, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        bSizer1701.Add( szr_view_schema1, 0, wx.EXPAND, 5 )

        bSizer181 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer891 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText77 = wx.StaticText( self.m_panel81, wx.ID_ANY, _(u"Type"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText77.Wrap( -1 )

        self.m_staticText77.SetMinSize( wx.Size( 150,-1 ) )

        bSizer891.Add( self.m_staticText77, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        routine_typeChoices = [ _(u"Procedure (doesn't return a result)"), _(u"Function (return a result)") ]
        self.routine_type = wx.Choice( self.m_panel81, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, routine_typeChoices, 0 )
        self.routine_type.SetSelection( 0 )
        bSizer891.Add( self.routine_type, 1, wx.ALL, 5 )


        bSizer181.Add( bSizer891, 1, wx.EXPAND, 5 )

        bSizer1161 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText78 = wx.StaticText( self.m_panel81, wx.ID_ANY, _(u"Return type"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText78.Wrap( -1 )

        bSizer1161.Add( self.m_staticText78, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        routine_return_typeChoices = []
        self.routine_return_type = wx.Choice( self.m_panel81, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, routine_return_typeChoices, 0 )
        self.routine_return_type.SetSelection( 0 )
        self.routine_return_type.Enable( False )

        bSizer1161.Add( self.routine_return_type, 1, wx.ALL, 5 )


        bSizer181.Add( bSizer1161, 1, wx.EXPAND, 5 )


        bSizer1701.Add( bSizer181, 0, wx.EXPAND, 5 )

        bSizer182 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText79 = wx.StaticText( self.m_panel81, wx.ID_ANY, _(u"Comment"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText79.Wrap( -1 )

        bSizer182.Add( self.m_staticText79, 0, wx.ALL, 5 )

        self.routine_comment = wx.TextCtrl( self.m_panel81, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_MULTILINE )
        bSizer182.Add( self.routine_comment, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer1701.Add( bSizer182, 1, wx.EXPAND, 5 )


        self.m_panel81.SetSizer( bSizer1701 )
        self.m_panel81.Layout()
        bSizer1701.Fit( self.m_panel81 )
        self.m_notebook11.AddPage( self.m_panel81, _(u"General"), True )
        self.m_panel82 = wx.Panel( self.m_notebook11, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer178 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer185 = wx.BoxSizer( wx.VERTICAL )


        bSizer178.Add( bSizer185, 1, wx.EXPAND, 5 )

        self.m_toolBar11 = wx.ToolBar( self.m_panel82, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORZ_TEXT|wx.TB_RIGHT|wx.TB_TEXT|wx.TB_VERTICAL )
        self.m_tool40 = self.m_toolBar11.AddTool( wx.ID_ANY, _(u"Insert"), wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Insert"), wx.EmptyString, None )

        self.m_tool41 = self.m_toolBar11.AddTool( wx.ID_ANY, _(u"Remove"), wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_tool42 = self.m_toolBar11.AddTool( wx.ID_ANY, _(u"Clear"), wx.Bitmap( u"icons/16x16/cross.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_toolBar11.Realize()

        bSizer178.Add( self.m_toolBar11, 0, wx.EXPAND, 5 )

        self.routine_parameters = wx.dataview.DataViewCtrl( self.m_panel82, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_dataViewColumn27 = self.routine_parameters.AppendTextColumn( _(u"#"), 0, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
        self.m_dataViewColumn28 = self.routine_parameters.AppendTextColumn( _(u"Name"), 0, wx.dataview.DATAVIEW_CELL_INERT, 600, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
        self.m_dataViewColumn29 = self.routine_parameters.AppendTextColumn( _(u"Datatype"), 0, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
        self.m_dataViewColumn30 = self.routine_parameters.AppendTextColumn( _(u"Context"), 0, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
        bSizer178.Add( self.routine_parameters, 1, wx.ALL|wx.EXPAND, 5 )


        self.m_panel82.SetSizer( bSizer178 )
        self.m_panel82.Layout()
        bSizer178.Fit( self.m_panel82 )
        self.m_notebook11.AddPage( self.m_panel82, _(u"Parameters"), False )
        self.m_panel86 = wx.Panel( self.m_notebook11, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer183 = wx.BoxSizer( wx.VERTICAL )

        self.panel_behavior_mysql_mariadb = wx.Panel( self.m_panel86, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer184 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer186 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText80 = wx.StaticText( self.panel_behavior_mysql_mariadb, wx.ID_ANY, _(u"Data access"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText80.Wrap( -1 )

        self.m_staticText80.SetMinSize( wx.Size( 150,-1 ) )

        bSizer186.Add( self.m_staticText80, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        behavior_data_accessChoices = [ _(u"CONTAINS SQL"), _(u"NO SQL"), _(u"READS SQL DATA"), _(u"MODIFIES SQL DATA"), wx.EmptyString, wx.EmptyString ]
        self.behavior_data_access = wx.Choice( self.panel_behavior_mysql_mariadb, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, behavior_data_accessChoices, 0 )
        self.behavior_data_access.SetSelection( 0 )
        bSizer186.Add( self.behavior_data_access, 0, wx.ALL, 5 )


        bSizer184.Add( bSizer186, 1, wx.EXPAND, 5 )

        bSizer1851 = wx.BoxSizer( wx.VERTICAL )

        self.behavior_deterministic = wx.CheckBox( self.panel_behavior_mysql_mariadb, wx.ID_ANY, _(u"Deterministic"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer1851.Add( self.behavior_deterministic, 1, wx.ALL, 5 )


        bSizer184.Add( bSizer1851, 1, wx.EXPAND, 5 )


        self.panel_behavior_mysql_mariadb.SetSizer( bSizer184 )
        self.panel_behavior_mysql_mariadb.Layout()
        bSizer184.Fit( self.panel_behavior_mysql_mariadb )
        bSizer183.Add( self.panel_behavior_mysql_mariadb, 0, wx.EXPAND | wx.ALL, 5 )

        self.panel_behavior_postgresql = wx.Panel( self.m_panel86, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer187 = wx.BoxSizer( wx.VERTICAL )

        bSizer188 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText81 = wx.StaticText( self.panel_behavior_postgresql, wx.ID_ANY, _(u"Language"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText81.Wrap( -1 )

        self.m_staticText81.SetMinSize( wx.Size( 150,-1 ) )

        bSizer188.Add( self.m_staticText81, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        behavior_postgresql_languageChoices = [ _(u"SQL"), _(u"PLPGSQL") ]
        self.behavior_postgresql_language = wx.Choice( self.panel_behavior_postgresql, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, behavior_postgresql_languageChoices, 0 )
        self.behavior_postgresql_language.SetSelection( 0 )
        bSizer188.Add( self.behavior_postgresql_language, 1, wx.ALL, 5 )


        bSizer187.Add( bSizer188, 1, wx.EXPAND, 5 )

        bSizer1881 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText811 = wx.StaticText( self.panel_behavior_postgresql, wx.ID_ANY, _(u"Volatility"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText811.Wrap( -1 )

        self.m_staticText811.SetMinSize( wx.Size( 150,-1 ) )

        bSizer1881.Add( self.m_staticText811, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        behavior_postgresql_volatilityChoices = [ _(u"VOLATILE"), _(u"STABLE"), _(u"IMMUTABLE"), wx.EmptyString ]
        self.behavior_postgresql_volatility = wx.Choice( self.panel_behavior_postgresql, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, behavior_postgresql_volatilityChoices, 0 )
        self.behavior_postgresql_volatility.SetSelection( 0 )
        bSizer1881.Add( self.behavior_postgresql_volatility, 1, wx.ALL, 5 )


        bSizer187.Add( bSizer1881, 1, wx.EXPAND, 5 )

        bSizer18811 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText8112 = wx.StaticText( self.panel_behavior_postgresql, wx.ID_ANY, _(u"Parallel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText8112.Wrap( -1 )

        self.m_staticText8112.SetMinSize( wx.Size( 150,-1 ) )

        bSizer18811.Add( self.m_staticText8112, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        behavior_postgresql_parallelChoices = [ _(u"UNSAFE"), _(u"RESTRICTED"), _(u"SAFE") ]
        self.behavior_postgresql_parallel = wx.Choice( self.panel_behavior_postgresql, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, behavior_postgresql_parallelChoices, 0 )
        self.behavior_postgresql_parallel.SetSelection( 0 )
        bSizer18811.Add( self.behavior_postgresql_parallel, 1, wx.ALL, 5 )


        bSizer187.Add( bSizer18811, 1, wx.EXPAND, 5 )

        bSizer192 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer196 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText87 = wx.StaticText( self.panel_behavior_postgresql, wx.ID_ANY, _(u"Cost"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText87.Wrap( -1 )

        self.m_staticText87.SetMinSize( wx.Size( 150,-1 ) )

        bSizer196.Add( self.m_staticText87, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.behavior_postgresql_cost = wx.SpinCtrlDouble( self.panel_behavior_postgresql, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 100, 0, 1 )
        self.behavior_postgresql_cost.SetDigits( 0 )
        bSizer196.Add( self.behavior_postgresql_cost, 1, wx.ALL, 5 )


        bSizer192.Add( bSizer196, 1, wx.EXPAND, 5 )

        bSizer193 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_staticText85 = wx.StaticText( self.panel_behavior_postgresql, wx.ID_ANY, _(u"Rows"), wx.DefaultPosition, wx.Size( 150,-1 ), 0 )
        self.m_staticText85.Wrap( -1 )

        bSizer193.Add( self.m_staticText85, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        self.behavior_postgresql_rows = wx.SpinCtrl( self.panel_behavior_postgresql, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 10, 0 )
        self.behavior_postgresql_rows.Enable( False )

        bSizer193.Add( self.behavior_postgresql_rows, 0, wx.ALL, 5 )


        bSizer192.Add( bSizer193, 1, wx.EXPAND, 5 )


        bSizer187.Add( bSizer192, 1, wx.EXPAND, 5 )


        self.panel_behavior_postgresql.SetSizer( bSizer187 )
        self.panel_behavior_postgresql.Layout()
        bSizer187.Fit( self.panel_behavior_postgresql )
        bSizer183.Add( self.panel_behavior_postgresql, 1, wx.EXPAND | wx.ALL, 5 )


        self.m_panel86.SetSizer( bSizer183 )
        self.m_panel86.Layout()
        bSizer183.Fit( self.m_panel86 )
        self.m_notebook11.AddPage( self.m_panel86, _(u"Behavior"), False )
        self.m_panel83 = wx.Panel( self.m_notebook11, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        Security = wx.BoxSizer( wx.VERTICAL )

        self.routine_definer_panel = wx.Panel( self.m_panel83, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        szr_view_definer1 = wx.BoxSizer( wx.HORIZONTAL )

        self.lbl_view_definer1 = wx.StaticText( self.routine_definer_panel, wx.ID_ANY, _(u"Definer"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lbl_view_definer1.Wrap( -1 )

        self.lbl_view_definer1.SetMinSize( wx.Size( 150,-1 ) )

        szr_view_definer1.Add( self.lbl_view_definer1, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        routine_definerChoices = []
        self.routine_definer = wx.ComboBox( self.routine_definer_panel, wx.ID_ANY, _(u"*"), wx.DefaultPosition, wx.DefaultSize, routine_definerChoices, 0 )
        szr_view_definer1.Add( self.routine_definer, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        self.routine_definer_panel.SetSizer( szr_view_definer1 )
        self.routine_definer_panel.Layout()
        szr_view_definer1.Fit( self.routine_definer_panel )
        Security.Add( self.routine_definer_panel, 0, wx.EXPAND | wx.ALL, 5 )

        self.routine_security_panel = wx.Panel( self.m_panel83, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        szr_view_sql_security1 = wx.BoxSizer( wx.HORIZONTAL )

        self.lbl_view_sql_security1 = wx.StaticText( self.routine_security_panel, wx.ID_ANY, _(u"SQL security"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lbl_view_sql_security1.Wrap( -1 )

        self.lbl_view_sql_security1.SetMinSize( wx.Size( 150,-1 ) )

        szr_view_sql_security1.Add( self.lbl_view_sql_security1, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

        routine_security_sqlChoices = [ _(u"DEFINER"), _(u"INVOKER") ]
        self.routine_security_sql = wx.Choice( self.routine_security_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, routine_security_sqlChoices, 0 )
        self.routine_security_sql.SetSelection( 0 )
        szr_view_sql_security1.Add( self.routine_security_sql, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


        self.routine_security_panel.SetSizer( szr_view_sql_security1 )
        self.routine_security_panel.Layout()
        szr_view_sql_security1.Fit( self.routine_security_panel )
        Security.Add( self.routine_security_panel, 0, wx.EXPAND | wx.ALL, 5 )


        self.m_panel83.SetSizer( Security )
        self.m_panel83.Layout()
        Security.Fit( self.m_panel83 )
        self.m_notebook11.AddPage( self.m_panel83, _(u"Security"), False )

        bSizer166.Add( self.m_notebook11, 1, wx.EXPAND | wx.ALL, 5 )


        self.m_panel73.SetSizer( bSizer166 )
        self.m_panel73.Layout()
        bSizer166.Fit( self.m_panel73 )
        self.m_panel74 = wx.Panel( self.m_splitter9, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer161 = wx.BoxSizer( wx.VERTICAL )

        self.routine_stc = wx.stc.StyledTextCtrl( self.m_panel74, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,-1 ), 0)
        self.routine_stc.SetUseTabs ( True )
        self.routine_stc.SetTabWidth ( 4 )
        self.routine_stc.SetIndent ( 4 )
        self.routine_stc.SetTabIndents( True )
        self.routine_stc.SetBackSpaceUnIndents( True )
        self.routine_stc.SetViewEOL( False )
        self.routine_stc.SetViewWhiteSpace( False )
        self.routine_stc.SetMarginWidth( 2, 0 )
        self.routine_stc.SetIndentationGuides( True )
        self.routine_stc.SetReadOnly( False )
        self.routine_stc.SetMarginWidth( 1, 0 )
        self.routine_stc.SetMarginType( 0, wx.stc.STC_MARGIN_NUMBER )
        self.routine_stc.SetMarginWidth( 0, self.routine_stc.TextWidth( wx.stc.STC_STYLE_LINENUMBER, "_99999" ) )
        self.routine_stc.MarkerDefine( wx.stc.STC_MARKNUM_FOLDER, wx.stc.STC_MARK_BOXPLUS )
        self.routine_stc.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDER, wx.BLACK)
        self.routine_stc.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDER, wx.WHITE)
        self.routine_stc.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.stc.STC_MARK_BOXMINUS )
        self.routine_stc.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.BLACK )
        self.routine_stc.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.WHITE )
        self.routine_stc.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERSUB, wx.stc.STC_MARK_EMPTY )
        self.routine_stc.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEREND, wx.stc.STC_MARK_BOXPLUS )
        self.routine_stc.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEREND, wx.BLACK )
        self.routine_stc.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEREND, wx.WHITE )
        self.routine_stc.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.stc.STC_MARK_BOXMINUS )
        self.routine_stc.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.BLACK)
        self.routine_stc.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.WHITE)
        self.routine_stc.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERMIDTAIL, wx.stc.STC_MARK_EMPTY )
        self.routine_stc.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERTAIL, wx.stc.STC_MARK_EMPTY )
        self.routine_stc.SetSelBackground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT ) )
        self.routine_stc.SetSelForeground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT ) )
        self.routine_stc.SetMinSize( wx.Size( -1,200 ) )

        bSizer161.Add( self.routine_stc, 1, wx.EXPAND | wx.ALL, 5 )


        self.m_panel74.SetSizer( bSizer161 )
        self.m_panel74.Layout()
        bSizer161.Fit( self.m_panel74 )
        self.m_splitter9.SplitHorizontally( self.m_panel73, self.m_panel74, 0 )
        bSizer160.Add( self.m_splitter9, 1, wx.EXPAND, 5 )

        bSizer911 = wx.BoxSizer( wx.HORIZONTAL )

        self.btn_routine_delete = wx.Button( self.panel_routine, wx.ID_ANY, _(u"Delete"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_routine_delete.Enable( False )

        bSizer911.Add( self.btn_routine_delete, 0, wx.ALL, 5 )

        self.btn_routine_cancel = wx.Button( self.panel_routine, wx.ID_ANY, _(u"Cancel"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_routine_cancel.Enable( False )

        bSizer911.Add( self.btn_routine_cancel, 0, wx.ALL, 5 )

        self.btn_routine_save = wx.Button( self.panel_routine, wx.ID_ANY, _(u"Save"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_routine_save.Enable( False )

        bSizer911.Add( self.btn_routine_save, 0, wx.ALL, 5 )


        bSizer160.Add( bSizer911, 0, wx.EXPAND, 5 )


        self.panel_routine.SetSizer( bSizer160 )
        self.panel_routine.Layout()
        bSizer160.Fit( self.panel_routine )
        self.MainFrameNotebook.AddPage( self.panel_routine, _(u"Routine"), False )
        MainFrameNotebookBitmap = wx.Bitmap( u"icons/16x16/code-folding.png", wx.BITMAP_TYPE_ANY )
        if ( MainFrameNotebookBitmap.IsOk() ):
            MainFrameNotebookImages.Add( MainFrameNotebookBitmap )
            self.MainFrameNotebook.SetPageImage( MainFrameNotebookIndex, MainFrameNotebookIndex )
            MainFrameNotebookIndex += 1

        self.panel_triggers = wx.Panel( self.MainFrameNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.MainFrameNotebook.AddPage( self.panel_triggers, _(u"Trigger"), False )
        MainFrameNotebookBitmap = wx.Bitmap( u"icons/16x16/cog.png", wx.BITMAP_TYPE_ANY )
        if ( MainFrameNotebookBitmap.IsOk() ):
            MainFrameNotebookImages.Add( MainFrameNotebookBitmap )
            self.MainFrameNotebook.SetPageImage( MainFrameNotebookIndex, MainFrameNotebookIndex )
            MainFrameNotebookIndex += 1

        self.panel_records = wx.Panel( self.MainFrameNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer61 = wx.BoxSizer( wx.VERTICAL )

        self.m_toolBar3 = wx.ToolBar( self.panel_records, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL|wx.TB_HORZ_TEXT )
        self.tool_refresh_records = self.m_toolBar3.AddTool( wx.ID_ANY, _(u"Refresh"), wx.Bitmap( u"icons/16x16/arrow_refresh.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_toolBar3.AddSeparator()

        self.tool_insert_record = self.m_toolBar3.AddTool( wx.ID_ANY, _(u"Add"), wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.tool_duplicate_record = self.m_toolBar3.AddTool( wx.ID_ANY, _(u"Duplicate"), wx.Bitmap( u"icons/16x16/page_copy_columns.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.tool_delete_record = self.m_toolBar3.AddTool( wx.ID_ANY, _(u"Remove"), wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_toolBar3.AddSeparator()

        self.chb_auto_apply = wx.CheckBox( self.m_toolBar3, wx.ID_ANY, _(u"Apply changes automatically"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.chb_auto_apply.SetValue(True)
        self.chb_auto_apply.SetToolTip( _(u"If enabled, table edits are applied immediately without pressing Apply or Cancel") )
        self.chb_auto_apply.SetHelpText( _(u"If enabled, table edits are applied immediately without pressing Apply or Cancel") )

        self.m_toolBar3.AddControl( self.chb_auto_apply )
        self.tool_apply_record = self.m_toolBar3.AddTool( wx.ID_ANY, _(u"Apply"), wx.Bitmap( u"icons/16x16/tick.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.tool_cancel_record = self.m_toolBar3.AddTool( wx.ID_ANY, _(u"Cancel"), wx.Bitmap( u"icons/16x16/cross.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_toolBar3.Realize()

        bSizer61.Add( self.m_toolBar3, 0, wx.EXPAND, 5 )

        bSizer94 = wx.BoxSizer( wx.HORIZONTAL )

        self.name_database_table = wx.StaticText( self.panel_records, wx.ID_ANY, _(u"{database_name}.{table_name} - rows {from_row} - {to_row} of {total_rows}"), wx.DefaultPosition, wx.DefaultSize, 0 )
        self.name_database_table.Wrap( -1 )

        bSizer94.Add( self.name_database_table, 0, wx.ALIGN_CENTER|wx.ALL, 5 )


        bSizer94.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.btn_first_records = wx.Button( self.panel_records, wx.ID_ANY, _(u"First"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

        self.btn_first_records.SetBitmap( wx.Bitmap( u"icons/16x16/resultset_first.png", wx.BITMAP_TYPE_ANY ) )
        bSizer94.Add( self.btn_first_records, 0, wx.ALL|wx.EXPAND, 5 )

        self.btn_prev_records = wx.Button( self.panel_records, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE|wx.BU_EXACTFIT )

        self.btn_prev_records.SetBitmap( wx.Bitmap( u"icons/16x16/arrow_left.png", wx.BITMAP_TYPE_ANY ) )
        bSizer94.Add( self.btn_prev_records, 0, wx.ALL|wx.EXPAND, 5 )

        self.limit_records = wx.SpinCtrl( self.panel_records, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 1000, 100 )
        bSizer94.Add( self.limit_records, 0, wx.ALL, 5 )

        self.btn_next_records = wx.Button( self.panel_records, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE|wx.BU_EXACTFIT|wx.BU_NOTEXT )

        self.btn_next_records.SetBitmap( wx.Bitmap( u"icons/16x16/resultset_next.png", wx.BITMAP_TYPE_ANY ) )
        bSizer94.Add( self.btn_next_records, 0, wx.ALL|wx.EXPAND, 5 )

        self.btn_last_records = wx.Button( self.panel_records, wx.ID_ANY, _(u"Last"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

        self.btn_last_records.SetBitmap( wx.Bitmap( u"icons/16x16/resultset_last.png", wx.BITMAP_TYPE_ANY ) )
        self.btn_last_records.SetBitmapPosition( wx.RIGHT )
        bSizer94.Add( self.btn_last_records, 0, wx.ALL|wx.EXPAND, 5 )


        bSizer61.Add( bSizer94, 0, wx.EXPAND, 5 )

        self.m_collapsiblePane1 = wx.CollapsiblePane( self.panel_records, wx.ID_ANY, _(u"Filters"), wx.DefaultPosition, wx.DefaultSize, wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE|wx.FULL_REPAINT_ON_RESIZE )
        self.m_collapsiblePane1.Collapse( True )

        bSizer831 = wx.BoxSizer( wx.VERTICAL )

        self.sql_query_filters = wx.stc.StyledTextCtrl( self.m_collapsiblePane1.GetPane(), wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,100 ), 0)
        self.sql_query_filters.SetUseTabs ( True )
        self.sql_query_filters.SetTabWidth ( 4 )
        self.sql_query_filters.SetIndent ( 4 )
        self.sql_query_filters.SetTabIndents( True )
        self.sql_query_filters.SetBackSpaceUnIndents( True )
        self.sql_query_filters.SetViewEOL( False )
        self.sql_query_filters.SetViewWhiteSpace( False )
        self.sql_query_filters.SetMarginWidth( 2, 0 )
        self.sql_query_filters.SetIndentationGuides( True )
        self.sql_query_filters.SetReadOnly( False )
        self.sql_query_filters.SetMarginWidth( 1, 0 )
        self.sql_query_filters.SetMarginWidth ( 0, 0 )
        self.sql_query_filters.MarkerDefine( wx.stc.STC_MARKNUM_FOLDER, wx.stc.STC_MARK_BOXPLUS )
        self.sql_query_filters.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDER, wx.BLACK)
        self.sql_query_filters.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDER, wx.WHITE)
        self.sql_query_filters.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.stc.STC_MARK_BOXMINUS )
        self.sql_query_filters.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.BLACK )
        self.sql_query_filters.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.WHITE )
        self.sql_query_filters.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERSUB, wx.stc.STC_MARK_EMPTY )
        self.sql_query_filters.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEREND, wx.stc.STC_MARK_BOXPLUS )
        self.sql_query_filters.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEREND, wx.BLACK )
        self.sql_query_filters.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEREND, wx.WHITE )
        self.sql_query_filters.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.stc.STC_MARK_BOXMINUS )
        self.sql_query_filters.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.BLACK)
        self.sql_query_filters.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.WHITE)
        self.sql_query_filters.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERMIDTAIL, wx.stc.STC_MARK_EMPTY )
        self.sql_query_filters.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERTAIL, wx.stc.STC_MARK_EMPTY )
        self.sql_query_filters.SetSelBackground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT ) )
        self.sql_query_filters.SetSelForeground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT ) )
        bSizer831.Add( self.sql_query_filters, 1, wx.EXPAND | wx.ALL, 5 )

        bSizer1591 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_button41 = wx.Button( self.m_collapsiblePane1.GetPane(), wx.ID_ANY, _(u"Apply"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

        self.m_button41.SetBitmap( wx.Bitmap( u"icons/16x16/tick.png", wx.BITMAP_TYPE_ANY ) )
        self.m_button41.SetToolTip( _(u"Apply filters in data\nCTRL+ENTER") )
        self.m_button41.SetHelpText( _(u"CTRL+ENTER") )

        bSizer1591.Add( self.m_button41, 0, wx.ALL, 5 )

        self.m_button56 = wx.Button( self.m_collapsiblePane1.GetPane(), wx.ID_ANY, _(u"Clear"), wx.DefaultPosition, wx.DefaultSize, wx.BORDER_NONE )

        self.m_button56.SetBitmap( wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ) )
        bSizer1591.Add( self.m_button56, 0, wx.ALL, 5 )


        bSizer831.Add( bSizer1591, 0, wx.EXPAND, 5 )


        self.m_collapsiblePane1.GetPane().SetSizer( bSizer831 )
        self.m_collapsiblePane1.GetPane().Layout()
        bSizer831.Fit( self.m_collapsiblePane1.GetPane() )
        bSizer61.Add( self.m_collapsiblePane1, 0, wx.ALL|wx.EXPAND, 5 )

        self.list_ctrl_table_records = TableRecordsDataViewCtrl( self.panel_records, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.dataview.DV_MULTIPLE )
        self.list_ctrl_table_records.SetFont( wx.Font( 10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        bSizer61.Add( self.list_ctrl_table_records, 1, wx.ALL|wx.EXPAND, 5 )


        self.panel_records.SetSizer( bSizer61 )
        self.panel_records.Layout()
        bSizer61.Fit( self.panel_records )
        self.menu_table_records = wx.Menu()
        self.m_menuItem13 = wx.MenuItem( self.menu_table_records, wx.ID_ANY, _(u"Insert row")+ u"\t" + u"Ins", wx.EmptyString, wx.ITEM_NORMAL )
        self.menu_table_records.Append( self.m_menuItem13 )

        self.m_menuItem14 = wx.MenuItem( self.menu_table_records, wx.ID_ANY, _(u"MyMenuItem"), wx.EmptyString, wx.ITEM_NORMAL )
        self.menu_table_records.Append( self.m_menuItem14 )

        self.menu_table_records.AppendSeparator()

        self.m_menuItem20 = wx.MenuItem( self.menu_table_records, wx.ID_ANY, _(u"MyMenuItem"), wx.EmptyString, wx.ITEM_NORMAL )
        self.menu_table_records.Append( self.m_menuItem20 )

        self.m_menu41 = wx.Menu()
        self.m_menuItem21 = wx.MenuItem( self.m_menu41, wx.ID_ANY, _(u"NULL"), wx.EmptyString, wx.ITEM_NORMAL )
        self.m_menu41.Append( self.m_menuItem21 )

        self.menu_table_records.AppendSubMenu( self.m_menu41, _(u"MyMenu") )

        self.panel_records.Bind( wx.EVT_RIGHT_DOWN, self.panel_recordsOnContextMenu )

        self.MainFrameNotebook.AddPage( self.panel_records, _(u"Data"), False )
        MainFrameNotebookBitmap = wx.Bitmap( u"icons/16x16/text_columns.png", wx.BITMAP_TYPE_ANY )
        if ( MainFrameNotebookBitmap.IsOk() ):
            MainFrameNotebookImages.Add( MainFrameNotebookBitmap )
            self.MainFrameNotebook.SetPageImage( MainFrameNotebookIndex, MainFrameNotebookIndex )
            MainFrameNotebookIndex += 1

        self.panel_query = wx.Panel( self.MainFrameNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer26 = wx.BoxSizer( wx.VERTICAL )

        self.m_splitter6 = wx.SplitterWindow( self.panel_query, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_3D )
        self.m_splitter6.Bind( wx.EVT_IDLE, self.m_splitter6OnIdle )

        self.m_panel52 = wx.Panel( self.m_splitter6, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer125 = wx.BoxSizer( wx.VERTICAL )

        self.m_toolBar2 = wx.ToolBar( self.m_panel52, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL|wx.TB_HORZ_TEXT )
        self.new_query = self.m_toolBar2.AddTool( wx.ID_ANY, _(u"Add"), wx.Bitmap( u"icons/16x16/add.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"New query"), wx.EmptyString, None )

        self.close_query = self.m_toolBar2.AddTool( wx.ID_ANY, _(u"Close"), wx.Bitmap( u"icons/16x16/delete.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Close query"), wx.EmptyString, None )

        self.m_toolBar2.AddSeparator()

        self.execute_statement = self.m_toolBar2.AddTool( wx.ID_ANY, _(u"Run"), wx.Bitmap( u"icons/16x16/arrow_right.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Execute"), wx.EmptyString, None )

        self.execute_all_statements = self.m_toolBar2.AddTool( wx.ID_ANY, _(u"Run all"), wx.Bitmap( u"icons/16x16/arrows_lefttoright.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Execute all statements"), wx.EmptyString, None )

        self.stop_statements = self.m_toolBar2.AddTool( wx.ID_ANY, _(u"Stop"), wx.Bitmap( u"icons/16x16/cancel.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, _(u"Stop"), wx.EmptyString, None )

        self.m_toolBar2.AddSeparator()

        self.save = self.m_toolBar2.AddTool( wx.ID_ANY, _(u"Save"), wx.Bitmap( u"icons/16x16/disk.png", wx.BITMAP_TYPE_ANY ), wx.NullBitmap, wx.ITEM_NORMAL, wx.EmptyString, wx.EmptyString, None )

        self.m_toolBar2.Realize()

        bSizer125.Add( self.m_toolBar2, 0, wx.EXPAND, 5 )

        bSizer150 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_splitter8 = wx.SplitterWindow( self.m_panel52, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_3D )
        self.m_splitter8.SetSashGravity( 1 )
        self.m_splitter8.Bind( wx.EVT_IDLE, self.m_splitter8OnIdle )

        self.m_panel70 = wx.Panel( self.m_splitter8, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer157 = wx.BoxSizer( wx.VERTICAL )

        self.notebook_query_editor = wx.Notebook( self.m_panel70, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_panel63 = wx.Panel( self.notebook_query_editor, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer146 = wx.BoxSizer( wx.VERTICAL )

        self.sql_query_editor = wx.stc.StyledTextCtrl( self.m_panel63, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        self.sql_query_editor.SetUseTabs ( True )
        self.sql_query_editor.SetTabWidth ( 4 )
        self.sql_query_editor.SetIndent ( 4 )
        self.sql_query_editor.SetTabIndents( True )
        self.sql_query_editor.SetBackSpaceUnIndents( True )
        self.sql_query_editor.SetViewEOL( False )
        self.sql_query_editor.SetViewWhiteSpace( False )
        self.sql_query_editor.SetMarginWidth( 2, 0 )
        self.sql_query_editor.SetIndentationGuides( True )
        self.sql_query_editor.SetReadOnly( False )
        self.sql_query_editor.SetMarginType ( 1, wx.stc.STC_MARGIN_SYMBOL )
        self.sql_query_editor.SetMarginMask ( 1, wx.stc.STC_MASK_FOLDERS )
        self.sql_query_editor.SetMarginWidth ( 1, 16)
        self.sql_query_editor.SetMarginSensitive( 1, True )
        self.sql_query_editor.SetProperty ( "fold", "1" )
        self.sql_query_editor.SetFoldFlags ( wx.stc.STC_FOLDFLAG_LINEBEFORE_CONTRACTED | wx.stc.STC_FOLDFLAG_LINEAFTER_CONTRACTED )
        self.sql_query_editor.SetMarginType( 0, wx.stc.STC_MARGIN_NUMBER )
        self.sql_query_editor.SetMarginWidth( 0, self.sql_query_editor.TextWidth( wx.stc.STC_STYLE_LINENUMBER, "_99999" ) )
        self.sql_query_editor.MarkerDefine( wx.stc.STC_MARKNUM_FOLDER, wx.stc.STC_MARK_BOXPLUS )
        self.sql_query_editor.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDER, wx.BLACK)
        self.sql_query_editor.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDER, wx.WHITE)
        self.sql_query_editor.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.stc.STC_MARK_BOXMINUS )
        self.sql_query_editor.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.BLACK )
        self.sql_query_editor.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.WHITE )
        self.sql_query_editor.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERSUB, wx.stc.STC_MARK_EMPTY )
        self.sql_query_editor.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEREND, wx.stc.STC_MARK_BOXPLUS )
        self.sql_query_editor.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEREND, wx.BLACK )
        self.sql_query_editor.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEREND, wx.WHITE )
        self.sql_query_editor.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.stc.STC_MARK_BOXMINUS )
        self.sql_query_editor.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.BLACK)
        self.sql_query_editor.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.WHITE)
        self.sql_query_editor.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERMIDTAIL, wx.stc.STC_MARK_EMPTY )
        self.sql_query_editor.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERTAIL, wx.stc.STC_MARK_EMPTY )
        self.sql_query_editor.SetSelBackground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT ) )
        self.sql_query_editor.SetSelForeground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT ) )
        bSizer146.Add( self.sql_query_editor, 1, wx.EXPAND | wx.ALL, 5 )


        self.m_panel63.SetSizer( bSizer146 )
        self.m_panel63.Layout()
        bSizer146.Fit( self.m_panel63 )
        self.notebook_query_editor.AddPage( self.m_panel63, _(u"a page"), False )

        bSizer157.Add( self.notebook_query_editor, 1, wx.EXPAND | wx.ALL, 5 )


        self.m_panel70.SetSizer( bSizer157 )
        self.m_panel70.Layout()
        bSizer157.Fit( self.m_panel70 )
        self.m_panel71 = wx.Panel( self.m_splitter8, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer1581 = wx.BoxSizer( wx.VERTICAL )

        self.tree_ctrl_query_history = wx.dataview.DataViewTreeCtrl( self.m_panel71, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.dataview.DV_NO_HEADER|wx.dataview.DV_ROW_LINES )
        self.tree_ctrl_query_history.SetMinSize( wx.Size( 200,-1 ) )

        bSizer1581.Add( self.tree_ctrl_query_history, 1, wx.ALL|wx.EXPAND, 5 )


        self.m_panel71.SetSizer( bSizer1581 )
        self.m_panel71.Layout()
        bSizer1581.Fit( self.m_panel71 )
        self.m_splitter8.SplitVertically( self.m_panel70, self.m_panel71, -480 )
        bSizer150.Add( self.m_splitter8, 1, wx.EXPAND, 5 )


        bSizer125.Add( bSizer150, 1, wx.EXPAND, 5 )


        self.m_panel52.SetSizer( bSizer125 )
        self.m_panel52.Layout()
        bSizer125.Fit( self.m_panel52 )
        self.m_panel53 = wx.Panel( self.m_splitter6, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_panel53.Hide()

        bSizer1261 = wx.BoxSizer( wx.VERTICAL )

        self.notebook_query_results = FlatNotebook( self.m_panel53, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )

        bSizer1261.Add( self.notebook_query_results, 1, wx.EXPAND | wx.ALL, 5 )


        self.m_panel53.SetSizer( bSizer1261 )
        self.m_panel53.Layout()
        bSizer1261.Fit( self.m_panel53 )
        self.m_splitter6.SplitHorizontally( self.m_panel52, self.m_panel53, -300 )
        bSizer26.Add( self.m_splitter6, 1, wx.EXPAND, 5 )


        self.panel_query.SetSizer( bSizer26 )
        self.panel_query.Layout()
        bSizer26.Fit( self.panel_query )
        self.MainFrameNotebook.AddPage( self.panel_query, _(u"Query"), False )
        MainFrameNotebookBitmap = wx.Bitmap( u"icons/16x16/arrow_right.png", wx.BITMAP_TYPE_ANY )
        if ( MainFrameNotebookBitmap.IsOk() ):
            MainFrameNotebookImages.Add( MainFrameNotebookBitmap )
            self.MainFrameNotebook.SetPageImage( MainFrameNotebookIndex, MainFrameNotebookIndex )
            MainFrameNotebookIndex += 1


        bSizer25.Add( self.MainFrameNotebook, 1, wx.ALL|wx.EXPAND, 5 )


        self.m_panel15.SetSizer( bSizer25 )
        self.m_panel15.Layout()
        bSizer25.Fit( self.m_panel15 )
        self.m_splitter4.SplitVertically( self.m_panel14, self.m_panel15, 320 )
        bSizer72.Add( self.m_splitter4, 1, wx.EXPAND, 5 )


        self.m_panel22.SetSizer( bSizer72 )
        self.m_panel22.Layout()
        bSizer72.Fit( self.m_panel22 )
        self.panel_sql_log = wx.Panel( self.m_splitter51, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,-1 ), wx.TAB_TRAVERSAL )
        sizer_log_sql = wx.BoxSizer( wx.VERTICAL )

        self.sql_query_logs = wx.stc.StyledTextCtrl( self.panel_sql_log, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,200 ), 0)
        self.sql_query_logs.SetUseTabs ( True )
        self.sql_query_logs.SetTabWidth ( 4 )
        self.sql_query_logs.SetIndent ( 4 )
        self.sql_query_logs.SetTabIndents( True )
        self.sql_query_logs.SetBackSpaceUnIndents( True )
        self.sql_query_logs.SetViewEOL( False )
        self.sql_query_logs.SetViewWhiteSpace( False )
        self.sql_query_logs.SetMarginWidth( 2, 0 )
        self.sql_query_logs.SetIndentationGuides( True )
        self.sql_query_logs.SetReadOnly( False )
        self.sql_query_logs.SetMarginWidth( 1, 0 )
        self.sql_query_logs.SetMarginType( 0, wx.stc.STC_MARGIN_NUMBER )
        self.sql_query_logs.SetMarginWidth( 0, self.sql_query_logs.TextWidth( wx.stc.STC_STYLE_LINENUMBER, "_99999" ) )
        self.sql_query_logs.MarkerDefine( wx.stc.STC_MARKNUM_FOLDER, wx.stc.STC_MARK_BOXPLUS )
        self.sql_query_logs.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDER, wx.BLACK)
        self.sql_query_logs.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDER, wx.WHITE)
        self.sql_query_logs.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.stc.STC_MARK_BOXMINUS )
        self.sql_query_logs.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.BLACK )
        self.sql_query_logs.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPEN, wx.WHITE )
        self.sql_query_logs.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERSUB, wx.stc.STC_MARK_EMPTY )
        self.sql_query_logs.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEREND, wx.stc.STC_MARK_BOXPLUS )
        self.sql_query_logs.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEREND, wx.BLACK )
        self.sql_query_logs.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEREND, wx.WHITE )
        self.sql_query_logs.MarkerDefine( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.stc.STC_MARK_BOXMINUS )
        self.sql_query_logs.MarkerSetBackground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.BLACK)
        self.sql_query_logs.MarkerSetForeground( wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.WHITE)
        self.sql_query_logs.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERMIDTAIL, wx.stc.STC_MARK_EMPTY )
        self.sql_query_logs.MarkerDefine( wx.stc.STC_MARKNUM_FOLDERTAIL, wx.stc.STC_MARK_EMPTY )
        self.sql_query_logs.SetSelBackground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT ) )
        self.sql_query_logs.SetSelForeground( True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT ) )
        sizer_log_sql.Add( self.sql_query_logs, 1, wx.EXPAND | wx.ALL, 5 )


        self.panel_sql_log.SetSizer( sizer_log_sql )
        self.panel_sql_log.Layout()
        sizer_log_sql.Fit( self.panel_sql_log )
        self.m_splitter51.SplitHorizontally( self.m_panel22, self.panel_sql_log, -200 )
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
        self.Bind( wx.EVT_MENU, self.on_settings, id = self.m_menuItem22.GetId() )
        self.Bind( wx.EVT_MENU, self.on_menu_about, id = self.m_menuItem15.GetId() )
        self.Bind( wx.EVT_TOOL, self.do_open_connection_manager, id = self.m_tool5.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_database_disconnect, id = self.m_tool4.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_refresh_database, id = self.tool_refresh_database.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_add_database, id = self.tool_add_database.GetId() )
        self.m_toggleBtn1.Bind( wx.EVT_TOGGLEBUTTON, self.on_toggle_read_only )
        self.MainFrameNotebook.Bind( wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_chaged )
        self.Bind( wx.EVT_TOOL, self.on_insert_table, id = self.tool_insert_table.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_clone_table, id = self.tool_clone_table.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_delete_table, id = self.tool_delete_table.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_insert_view, id = self.tool_insert_view.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_clone_view, id = self.tool_clone_view.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_delete_view, id = self.tool_delete_view.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_insert_procedure, id = self.tool_insert_procedure.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_clone_procedure, id = self.tool_clone_procedure.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_delete_procedure, id = self.tool_delete_procedure.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_insert_function, id = self.tool_insert_function.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_clone_function, id = self.tool_clone_function.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_delete_function, id = self.tool_delete_function.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_insert_view, id = self.tool_insert_trigger.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_clone_view, id = self.tool_clone_trigger.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_delete_view, id = self.tool_delete_trigger.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_insert_view, id = self.tool_insert_event.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_clone_view, id = self.tool_clone_event.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_delete_view, id = self.tool_delete_event.GetId() )
        self.btn_cancel_database.Bind( wx.EVT_BUTTON, self.on_cancel_database )
        self.btn_delete_database.Bind( wx.EVT_BUTTON, self.on_delete_database )
        self.btn_apply_database.Bind( wx.EVT_BUTTON, self.on_apply_database )
        self.Bind( wx.EVT_TOOL, self.on_delete_index, id = self.m_tool43.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_clear_index, id = self.m_tool44.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_insert_foreign_key, id = self.m_tool49.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_delete_foreign_key, id = self.m_tool431.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_clear_foreign_key, id = self.m_tool441.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_insert_check, id = self.m_tool491.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_delete_check, id = self.m_tool4311.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_clear_check, id = self.m_tool4411.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_insert_column, id = self.tool_add_column.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_delete_column, id = self.tool_remove_column.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_move_up_column, id = self.tool_move_up_column.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_move_down_column, id = self.tool_move_down_column.GetId() )
        self.btn_delete_table.Bind( wx.EVT_BUTTON, self.on_delete_table )
        self.btn_cancel_table.Bind( wx.EVT_BUTTON, self.on_cancel_table )
        self.btn_apply_table.Bind( wx.EVT_BUTTON, self.do_apply_table )
        self.Bind( wx.EVT_TOOL, self.on_routine_parameters_insert, id = self.m_tool40.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_routine_parameters_delete, id = self.m_tool41.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_routine_parameters_clear, id = self.m_tool42.GetId() )
        self.btn_routine_delete.Bind( wx.EVT_BUTTON, self.on_routine_delete )
        self.btn_routine_cancel.Bind( wx.EVT_BUTTON, self.on_routine_cancel )
        self.btn_routine_save.Bind( wx.EVT_BUTTON, self.on_routine_save )
        self.Bind( wx.EVT_TOOL, self.on_refresh_records, id = self.tool_refresh_records.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_insert_record, id = self.tool_insert_record.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_duplicate_record, id = self.tool_duplicate_record.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_delete_record, id = self.tool_delete_record.GetId() )
        self.chb_auto_apply.Bind( wx.EVT_CHECKBOX, self.on_auto_apply )
        self.Bind( wx.EVT_TOOL, self.on_apply_record, id = self.tool_apply_record.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_cancel_record, id = self.tool_cancel_record.GetId() )
        self.btn_first_records.Bind( wx.EVT_BUTTON, self.on_first_records )
        self.btn_prev_records.Bind( wx.EVT_BUTTON, self.on_prev_records )
        self.btn_next_records.Bind( wx.EVT_BUTTON, self.on_next_records )
        self.btn_last_records.Bind( wx.EVT_BUTTON, self.on_last_records )
        self.m_collapsiblePane1.Bind( wx.EVT_COLLAPSIBLEPANE_CHANGED, self.on_collapsible_pane_changed )
        self.m_button41.Bind( wx.EVT_BUTTON, self.on_apply_filters )
        self.m_button56.Bind( wx.EVT_BUTTON, self.on_clear_filters )
        self.Bind( wx.EVT_TOOL, self.on_new_query, id = self.new_query.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_close_query, id = self.close_query.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_execute_statement, id = self.execute_statement.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_execute_statements, id = self.execute_all_statements.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_stop_statements, id = self.stop_statements.GetId() )
        self.Bind( wx.EVT_TOOL, self.on_save, id = self.save.GetId() )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def do_close( self, event ):
        event.Skip()

    def on_settings( self, event ):
        event.Skip()

    def on_menu_about( self, event ):
        event.Skip()

    def do_open_connection_manager( self, event ):
        event.Skip()

    def on_database_disconnect( self, event ):
        event.Skip()

    def on_refresh_database( self, event ):
        event.Skip()

    def on_add_database( self, event ):
        event.Skip()

    def on_toggle_read_only( self, event ):
        event.Skip()

    def on_page_chaged( self, event ):
        event.Skip()

    def on_insert_table( self, event ):
        event.Skip()

    def on_clone_table( self, event ):
        event.Skip()

    def on_delete_table( self, event ):
        event.Skip()

    def on_insert_view( self, event ):
        event.Skip()

    def on_clone_view( self, event ):
        event.Skip()

    def on_delete_view( self, event ):
        event.Skip()

    def on_insert_procedure( self, event ):
        event.Skip()

    def on_clone_procedure( self, event ):
        event.Skip()

    def on_delete_procedure( self, event ):
        event.Skip()

    def on_insert_function( self, event ):
        event.Skip()

    def on_clone_function( self, event ):
        event.Skip()

    def on_delete_function( self, event ):
        event.Skip()







    def on_cancel_database( self, event ):
        event.Skip()

    def on_delete_database( self, event ):
        event.Skip()

    def on_apply_database( self, event ):
        event.Skip()

    def on_delete_index( self, event ):
        event.Skip()

    def on_clear_index( self, event ):
        event.Skip()

    def on_insert_foreign_key( self, event ):
        event.Skip()

    def on_delete_foreign_key( self, event ):
        event.Skip()

    def on_clear_foreign_key( self, event ):
        event.Skip()

    def on_insert_check( self, event ):
        event.Skip()

    def on_delete_check( self, event ):
        event.Skip()

    def on_clear_check( self, event ):
        event.Skip()

    def on_insert_column( self, event ):
        event.Skip()

    def on_delete_column( self, event ):
        event.Skip()

    def on_move_up_column( self, event ):
        event.Skip()

    def on_move_down_column( self, event ):
        event.Skip()


    def on_cancel_table( self, event ):
        event.Skip()

    def do_apply_table( self, event ):
        event.Skip()

    def on_routine_parameters_insert( self, event ):
        event.Skip()

    def on_routine_parameters_delete( self, event ):
        event.Skip()

    def on_routine_parameters_clear( self, event ):
        event.Skip()

    def on_routine_delete( self, event ):
        event.Skip()

    def on_routine_cancel( self, event ):
        event.Skip()

    def on_routine_save( self, event ):
        event.Skip()

    def on_refresh_records( self, event ):
        event.Skip()

    def on_insert_record( self, event ):
        event.Skip()

    def on_duplicate_record( self, event ):
        event.Skip()

    def on_delete_record( self, event ):
        event.Skip()

    def on_auto_apply( self, event ):
        event.Skip()

    def on_apply_record( self, event ):
        event.Skip()

    def on_cancel_record( self, event ):
        event.Skip()

    def on_first_records( self, event ):
        event.Skip()

    def on_prev_records( self, event ):
        event.Skip()

    def on_next_records( self, event ):
        event.Skip()

    def on_last_records( self, event ):
        event.Skip()

    def on_collapsible_pane_changed( self, event ):
        event.Skip()

    def on_apply_filters( self, event ):
        event.Skip()

    def on_clear_filters( self, event ):
        event.Skip()

    def on_new_query( self, event ):
        event.Skip()

    def on_close_query( self, event ):
        event.Skip()

    def on_execute_statement( self, event ):
        event.Skip()

    def on_execute_statements( self, event ):
        event.Skip()

    def on_stop_statements( self, event ):
        event.Skip()

    def on_save( self, event ):
        event.Skip()

    def m_splitter51OnIdle( self, event ):
        self.m_splitter51.SetSashPosition( -200 )
        self.m_splitter51.Unbind( wx.EVT_IDLE )

    def m_splitter4OnIdle( self, event ):
        self.m_splitter4.SetSashPosition( 320 )
        self.m_splitter4.Unbind( wx.EVT_IDLE )

    def m_panel14OnContextMenu( self, event ):
        self.m_panel14.PopupMenu( self.m_menu5, event.GetPosition() )

    def m_splitter7OnIdle( self, event ):
        self.m_splitter7.SetSashPosition( 200 )
        self.m_splitter7.Unbind( wx.EVT_IDLE )

    def m_splitter41OnIdle( self, event ):
        self.m_splitter41.SetSashPosition( 200 )
        self.m_splitter41.Unbind( wx.EVT_IDLE )

    def panel_table_columnsOnContextMenu( self, event ):
        self.panel_table_columns.PopupMenu( self.menu_table_columns, event.GetPosition() )

    def m_splitter11OnIdle( self, event ):
        self.m_splitter11.SetSashPosition( 0 )
        self.m_splitter11.Unbind( wx.EVT_IDLE )

    def m_splitter9OnIdle( self, event ):
        self.m_splitter9.SetSashPosition( 0 )
        self.m_splitter9.Unbind( wx.EVT_IDLE )

    def panel_recordsOnContextMenu( self, event ):
        self.panel_records.PopupMenu( self.menu_table_records, event.GetPosition() )

    def m_splitter6OnIdle( self, event ):
        self.m_splitter6.SetSashPosition( -300 )
        self.m_splitter6.Unbind( wx.EVT_IDLE )

    def m_splitter8OnIdle( self, event ):
        self.m_splitter8.SetSashPosition( -480 )
        self.m_splitter8.Unbind( wx.EVT_IDLE )


###########################################################################
## Class MyPanel1
###########################################################################

class MyPanel1 ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )


    def __del__( self ):
        pass


###########################################################################
## Class Trash
###########################################################################

class Trash ( wx.Frame ):

    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer147 = wx.BoxSizer( wx.VERTICAL )

        bSizer152 = wx.BoxSizer( wx.VERTICAL )


        bSizer147.Add( bSizer152, 1, wx.EXPAND, 5 )

        self.m_panel821 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer96 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer14811 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer14811.Add( ( 0, 0), 1, wx.EXPAND, 5 )


        bSizer14811.Add( ( 0, 0), 0, wx.EXPAND, 5 )


        bSizer96.Add( bSizer14811, 0, wx.EXPAND, 5 )

        bSizer164 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer96.Add( bSizer164, 0, wx.EXPAND, 5 )

        bSizer92 = wx.BoxSizer( wx.HORIZONTAL )


        bSizer96.Add( bSizer92, 0, wx.EXPAND, 5 )


        self.m_panel821.SetSizer( bSizer96 )
        self.m_panel821.Layout()
        bSizer96.Fit( self.m_panel821 )
        bSizer147.Add( self.m_panel821, 1, wx.EXPAND | wx.ALL, 5 )

        self.database_read_only_panel = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer148 = wx.BoxSizer( wx.HORIZONTAL )

        self.database_read_only = wx.CheckBox( self.database_read_only_panel, wx.ID_ANY, _(u"Read Only"), wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer148.Add( self.database_read_only, 0, wx.ALIGN_CENTER|wx.ALL, 5 )


        self.database_read_only_panel.SetSizer( bSizer148 )
        self.database_read_only_panel.Layout()
        bSizer148.Fit( self.database_read_only_panel )
        bSizer147.Add( self.database_read_only_panel, 0, wx.EXPAND | wx.ALL, 5 )


        self.SetSizer( bSizer147 )
        self.Layout()
        self.m_menu15 = wx.Menu()
        self.Bind( wx.EVT_RIGHT_DOWN, self.TrashOnContextMenu )


        self.Centre( wx.BOTH )

    def __del__( self ):
        pass

    def TrashOnContextMenu( self, event ):
        self.PopupMenu( self.m_menu15, event.GetPosition() )


