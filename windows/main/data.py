import wx
import wx.dataview

from models.database import Table
from models.session import Session
from windows.main import CURRENT_TABLE, CURRENT_SESSION


class TableDataController:
    app = wx.GetApp()

    def __init__(self, list_ctrl_data: wx.dataview.DataViewCtrl):

        self.list_ctrl_data = list_ctrl_data
        # self.list_ctrl_table_columns.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        # self.list_ctrl_table_columns.Bind(wx.dataview.EVT_DATAVIEW_ITEM_EDITING_DONE, self.on_editing_done)
        # self.list_ctrl_table_columns.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self.on_editing_done)

        CURRENT_SESSION.subscribe(self._load_session)
        # CURRENT_SESSION.subscribe(self._update_columns)
        #
        # CURRENT_DATABASE.subscribe(self._update_columns)
        CURRENT_TABLE.subscribe(self._load_table)

    def _load_session(self, session: Session):
        self.session = session
        # if self.session.engine == SessionEngine.MYSQL:
        #     self.engine_data_type = MySQLDataType
        # if self.session.engine == SessionEngine.SQLITE:
        #     self.engine_data_type = SQLiteDataType
        #
        #     self.list_ctrl_table_columns.GetColumn(4).SetFlag(wx.dataview.DATAVIEW_COL_HIDDEN)
        #     self.list_ctrl_table_columns.GetColumn(6).SetFlag(wx.dataview.DATAVIEW_COL_HIDDEN)
        #     self.list_ctrl_table_columns.GetColumn(8).SetFlag(wx.dataview.DATAVIEW_COL_HIDDEN)

        # self.model = ColumnModel(self.engine_data_type)
        # self.list_ctrl_table_columns.AssociateModel(self.model)

    def _load_table(self, table: Table):
        # self.m_dataViewColumn2 = self.list_ctrl_table_columns.AppendTextColumn( _(u"#"), 0, wx.dataview.DATAVIEW_CELL_INERT, -1, wx.ALIGN_RIGHT, wx.dataview.DATAVIEW_COL_RESIZABLE )
        # 		self.m_dataViewColumn3 = self.list_ctrl_table_columns.AppendTextColumn( _(u"Name"), 1, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
        # 		self.m_dataViewColumn4 = self.list_ctrl_table_columns.AppendTextColumn( _(u"Data type"), 2, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_CENTER, wx.dataview.DATAVIEW_COL_RESIZABLE )
        # 		self.m_dataViewColumn5 = self.list_ctrl_table_columns.AppendTextColumn( _(u"Length/Set"), 3, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE )
        # 		self.m_dataViewCol

        # while self.list_ctrl_data.GetChildren() > 0:
        #     self.list_ctrl_data.RemoveChild()
        print("Load table", table)
        if table is not None :

            while self.list_ctrl_data.GetColumnCount() > 0:
                self.list_ctrl_data.DeleteColumn(self.list_ctrl_data.GetColumn(0))

            for i, column in enumerate(table.columns):
                self.list_ctrl_data.AppendTextColumn(column.name, i, wx.dataview.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, wx.dataview.DATAVIEW_COL_RESIZABLE)



            # for row in self.session.statement.select_table(table) :
            #     result = []
            #     for column in table.columns:
            #         result.append(str(row[column.name]))
            #
            #
            #     self.list_ctrl_data.AppendItem(result)




