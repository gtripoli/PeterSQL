import os
from typing import List, Dict, Any, Optional, Union

import yaml

from helpers.observables import ObservableList

from structures.session import (
    Session,
    SessionEngine,
    CredentialsConfiguration,
    SourceConfiguration,
    SSHTunnelConfiguration,
)

WORKDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SESSIONS_CONFIG_FILE = os.path.join(WORKDIR, "sessions.yml")


class SessionManagerRepository:
    def __init__(self):
        self.sessions: ObservableList[Session] = ObservableList([])
        self.refresh()

    def refresh(self) -> List[Session]:
        payload = self._read_sessions_file()
        sessions = [self.session_from_dict(index, data) for index, data in enumerate(payload)]
        self.sessions.set_value(sessions)
        return sessions

    def _read_sessions_file(self) -> List[Dict[str, Any]]:
        try:
            sessions = yaml.full_load(open(SESSIONS_CONFIG_FILE))
            return sessions or []
        except Exception:
            return []

    def _write_sessions_file(self, sessions: List[Session]) -> None:
        payload = [self.session_to_dict(session) for session in sessions]
        with open(SESSIONS_CONFIG_FILE, 'w') as file_handler:
            yaml.dump(payload, file_handler, sort_keys=False)

    def load_sessions(self) -> List[Session]:
        return self.refresh()

    def save_session(self, session: Session) -> List[Session]:
        self.sessions.append(session, replace_existing=True)

        self._write_sessions_file(list(self.sessions.get_value()))

        return self.load_sessions()

    def delete_session(self, session: Session) -> List[Session]:
        sessions = list(self.sessions.get_value())
        for existing in list(sessions):
            if existing == session:
                sessions.remove(existing)
                break
        self._write_sessions_file(sessions)
        self.sessions.set_value(sessions)
        return sessions

    def session_from_dict(self, index: int, data: Dict[str, Any]) -> Session:
        engine = SessionEngine.from_name(data['engine']) if data.get('engine') else None

        # Convert configuration
        configuration: Optional[Union[CredentialsConfiguration, SourceConfiguration]] = None
        if data.get('configuration'):
            config_data = data['configuration']
            if engine in [SessionEngine.MYSQL, SessionEngine.MARIADB, SessionEngine.POSTGRESQL]:
                configuration = CredentialsConfiguration(**config_data)
            elif engine == SessionEngine.SQLITE:
                configuration = SourceConfiguration(**config_data)

        ssh_config = self._build_ssh_configuration(data.get('ssh_tunnel', {}))

        return Session(
            id=index,
            name=data['name'],
            engine=engine,
            configuration=configuration,
            comments=data.get('comments'),
            ssh_tunnel=ssh_config,
        )

    def session_to_dict(self, session: Session) -> Dict[str, Any]:
        """Convert Session object to dictionary"""
        return session.to_dict()

    def _build_ssh_configuration(self, data: Dict[str, Any]) -> Optional[SSHTunnelConfiguration]:
        if not data:
            return None

        try:
            return SSHTunnelConfiguration(
                enabled=bool(data.get('enabled')),
                executable=data.get('executable', 'ssh'),
                hostname=data.get('hostname', ''),
                port=int(data.get('port', 22)),
                username=data.get('username', ''),
                password=data.get('password', ''),
                local_port=int(data.get('local_port', 0)),
            )
        except (TypeError, ValueError):
            return None
