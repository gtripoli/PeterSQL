import copy

from typing import List, Union, Dict, Callable, Optional

import wx
import wx.dataview

from gettext import gettext as _

from icons import ImageList, IconList

from windows import SessionManagerView
from windows.main import SESSIONS

from helpers.logger import logger
from helpers.bindings import AbstractModel
from helpers.observables import Observable, ObservableArray, debounce

from models.session import SessionEngine, Session, CredentialsConfiguration, SourceConfiguration

NEW_SESSION: Observable[Session] = Observable()
CURRENT_SESSION: Observable[Session] = Observable()


class SessionTreeController():
    on_select: Callable = None
    on_active: Callable = None

    def __init__(self, session_tree_ctrl: wx.dataview.TreeListCtrl, sessions: List):
        self.session_tree_ctrl = session_tree_ctrl
        self.session_tree_ctrl.SetImageList(ImageList)
        self.session_tree_root = self.session_tree_ctrl.GetRootItem()

        self.session_tree_ctrl.Bind(wx.dataview.EVT_TREELIST_SELECTION_CHANGED, self._on_item_select)
        self.session_tree_ctrl.Bind(wx.dataview.EVT_TREELIST_ITEM_ACTIVATED, self._on_item_active)

        self.sessions = ObservableArray(self._build_session_list(sessions))
        self.sessions.subscribe(self._load_sessions, Observable.CallbackEvent.AFTER_CHANGE, execute_immediately=True)

    def _build_session_list(self, sessions: List[Dict[str, Union[Dict, str]]], prefix: int = None):
        results = []
        for index, session in enumerate(sessions):
            if isinstance(session, str):
                results.append(session)

            elif session.get("sessions"):
                results.append({
                    "name": session['name'],
                    'sessions': self._build_session_list(session["sessions"], prefix=index)
                })

            else:
                engine = SessionEngine(session['engine'])
                if engine in [SessionEngine.MYSQL, SessionEngine.MARIADB]:
                    configuration = CredentialsConfiguration(**session["configuration"])
                elif engine == SessionEngine.SQLITE:
                    configuration = SourceConfiguration(**session["configuration"])

                results.append(
                    Session(
                        _id=f"{f'{prefix}_' if prefix is not None else ''}{index}",
                        name=session["name"],
                        engine=engine,
                        comments=session["comments"],
                        configuration=configuration
                    )
                )

        return results

    def _load_sessions(self, sessions: Union[List[Session], Dict]):
        self.session_tree_ctrl.DeleteAllItems()

        for session in sessions:
            if isinstance(session, dict):
                self._create_session_folder(session.get("name"), session.get("sessions", []))
            elif isinstance(session, Session):
                self._create_session_item(session)
            elif isinstance(session, str):
                self._create_session_new(session)

    def _create_session_folder(self, name: str, sessions: List[Session], parent=None):
        if parent is None:
            parent = self.session_tree_root

        item = self.session_tree_ctrl.AppendItem(parent, icon=wx.dataview.DataViewIconText(name))
        for session in sessions:
            self._create_session_item(session, parent=item)

    def _create_session_item(self, session: Session, parent=None):
        parent = parent or self.session_tree_root

        icon_index = None
        if session.engine == SessionEngine.MYSQL:
            icon_index = IconList.ENGINE_MYSQL
        elif session.engine == SessionEngine.MARIADB:
            icon_index = IconList.ENGINE_MARIADB
        elif session.engine == SessionEngine.SQLITE:
            icon_index = IconList.ENGINE_SQLITE

        bitmap = ImageList.GetBitmap(icon_index)

        item = self.session_tree_ctrl.AppendItem(parent, session.name, icon_index)
        self.session_tree_ctrl.SetItemData(item, session)

    def _create_session_new(self, label: str, parent=None):
        parent = parent or self.session_tree_root

        item = self.session_tree_ctrl.AppendItem(parent, label)
        self.session_tree_ctrl.UnselectAll()
        self.session_tree_ctrl.Select(item)
        return item

    def _on_item_select(self, event):
        item = event.GetItem()
        CURRENT_SESSION.set_value(self.session_tree_ctrl.GetItemData(item))
        if self.on_select is not None:
            self.on_select(event)

    def _on_item_active(self, event):
        item = event.GetItem()
        CURRENT_SESSION.set_value(self.session_tree_ctrl.GetItemData(item))
        if self.on_active is not None:
            self.on_active(event)


class SessionManagerModel(AbstractModel):
    def __init__(self):
        self.name = Observable()
        self.engine = Observable(default=SessionEngine.MYSQL.value)
        self.hostname = Observable()
        self.username = Observable()
        self.password = Observable()
        self.port = Observable(default=3306)
        self.filename = Observable()
        self.comments = Observable()

        debounce(
            self.name, self.engine, self.hostname, self.username, self.password, self.port, self.filename, self.comments,
            callback=self.build_session
        )

        CURRENT_SESSION.subscribe(self.clear, Observable.CallbackEvent.BEFORE_CHANGE)
        CURRENT_SESSION.subscribe(self.populate)

    def clear(self, *args):
        for field in [self.name, self.engine, self.hostname, self.username, self.password, self.port, self.filename, self.comments]:
            field.set_value(None)

    def populate(self, session: Session):
        if not session:
            return

        self.name.set_value(session.name)
        self.engine.set_value(session.engine.value)
        self.comments.set_value(session.comments)

        if isinstance(session.configuration, CredentialsConfiguration):
            self.hostname.set_value(session.configuration.hostname)
            self.username.set_value(session.configuration.username)
            self.password.set_value(session.configuration.password)
            self.port.set_value(session.configuration.port)

        elif isinstance(session.configuration, SourceConfiguration):
            self.filename.set_value(session.configuration.filename)

    def build_session(self, *args):
        if self.engine.is_empty:
            return

        new_session = None
        session_engine = SessionEngine(self.engine.get_value())

        if (current_session := CURRENT_SESSION.get_value()) is None:

            if session_engine in [SessionEngine.MYSQL, SessionEngine.MARIADB] and not any([
                self.name.is_empty, self.hostname.is_empty, self.username.is_empty, self.password.is_empty
            ]):
                new_session = Session(
                    name=self.name.get_value(),
                    engine=session_engine,
                    comments=self.comments.get_value(),
                    configuration=CredentialsConfiguration(
                        hostname=self.hostname.get_value(),
                        username=self.username.get_value(),
                        password=self.password.get_value(),
                        port=self.port.get_value()
                    )
                )
            elif self.engine.get_value() == SessionEngine.SQLITE.value and not self.filename.is_empty:
                new_session = Session(
                    name=self.name.get_value(),
                    engine=session_engine,
                    comments=self.comments.get_value(),
                    configuration=SourceConfiguration(
                        filename=self.filename.get_value()
                    )
                )
        else:
            modified = copy.copy(current_session)
            modified.name = self.name.get_value()
            modified.engine = session_engine
            modified.comments = self.comments.get_value()

            if session_engine in [SessionEngine.MYSQL, SessionEngine.MARIADB]:
                modified.configuration = CredentialsConfiguration(
                    hostname=self.hostname.get_value(),
                    username=self.username.get_value(),
                    password=self.password.get_value(),
                    port=self.port.get_value()
                )
            elif modified.engine == SessionEngine.SQLITE:
                modified.configuration = SourceConfiguration(
                    filename=self.filename.get_value()
                )

            if modified.is_valid() and modified != current_session:
                new_session = modified

        NEW_SESSION.set_value(new_session)


class SessionManagerController(SessionManagerView):
    def __init__(self, parent, sessions: List):
        super().__init__(parent)
        self.app = wx.GetApp()

        self.Bind(wx.EVT_CLOSE, self.on_exit)

        self.session_tree_controller = SessionTreeController(self.session_tree_ctrl, sessions=sessions)
        self.session_tree_controller.on_active = self.on_open

        self.session_tree_controller.sessions.subscribe(self.on_change_sessions_list)

        self.session_manager_model = SessionManagerModel()
        self.session_manager_model.bind_controls(
            name=self.name,
            engine=(self.engine, dict(initial=[engine.value for engine in SessionEngine])),
            hostname=self.hostname, port=self.port, username=self.username, password=self.password,
            filename=self.filename, comments=self.comments,
        )
        self.session_manager_model.engine.subscribe(self.on_change_engine)

        CURRENT_SESSION.subscribe(self.on_change_current_session)
        NEW_SESSION.subscribe(self.on_change_new_session)

    def on_change_engine(self, value):
        self.panel_credentials.Show(value in [SessionEngine.MYSQL.value, SessionEngine.MARIADB.value])
        self.panel_source.Show(value == SessionEngine.SQLITE.value)
        self.panel_source.GetParent().Layout()

    def on_create(self, *args):
        NEW_SESSION.set_value(None)
        CURRENT_SESSION.set_value(None)
        self.session_tree_controller.sessions.append(_("New Session"))
        self.name.SetFocus()

    def on_change_sessions_list(self, sessions: List[Session]):
        self.btn_create.Enable(not isinstance(sessions[-1], str))

    def on_change_current_session(self, session: Session):
        self.btn_open.Enable(bool(session and session.is_valid()))
        self.btn_delete.Enable(bool(session))

    def on_change_new_session(self, session: Session):
        self.btn_save.Enable(bool(session and session.is_valid()))
        self.btn_open.Enable(bool(session and session.is_valid()))

    def on_save(self, *args):
        session = NEW_SESSION.get_value()
        if not session:
            return False

        dialog = wx.MessageDialog(None,
                                  message=_(f'Do you want save the session {session.name}?'),
                                  style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION
                                  )

        if dialog.ShowModal() != wx.ID_YES:
            return False


        if session._id is None:
            self.session_tree_controller.sessions.append(session)
        else:
            index = self.session_tree_controller.sessions.find(lambda s: isinstance(s, Session) and s._id == session.id)
            self.session_tree_controller.sessions.replace(index, session)

        NEW_SESSION.set_value(None)
        CURRENT_SESSION.set_value(session)

        self.app.settings.set_value("sessions", value=self.session_tree_controller.sessions.get_value())

        return True

    def on_open(self, event):
        if NEW_SESSION.get_value() and not self.on_save(event):
            return
        session = CURRENT_SESSION.get_value()
        if session:
            try:
                self.app.verify_connection(session)
            except Exception as ex:
                logger.error(ex, exc_info=True)
            else:
                self.do_open_session(session)

    def on_delete(self, *args):
        session = CURRENT_SESSION.get_value()
        if not session:
            return
        dialog = wx.MessageDialog(None,
                                  message=_(f'Do you want delete the session {session.name}?'),
                                  style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION
                                  )
        if dialog.ShowModal() == wx.ID_YES:
            self.session_tree_controller.sessions.filter(lambda s: isinstance(s, Session) and s.id != session.id)
            NEW_SESSION.set_value(None)
            CURRENT_SESSION.set_value(None)
            self.app.settings.set_value("sessions", value=self.session_tree_controller.sessions.get_value())

    def do_open_session(self, session: Session):
        if not self.GetParent():
            self.app.open_main_frame()

        SESSIONS.append(session)
        self.Close()

    def on_exit(self, event):
        if not self.app.main_frame:
            self.app.do_exit(event)
        else:
            self.Destroy()

        event.Skip()
