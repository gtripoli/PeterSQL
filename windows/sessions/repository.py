import os
import yaml
from typing import List, Dict, Any, Optional, Union

from structures.session import Session, SessionEngine, CredentialsConfiguration, SourceConfiguration

WORKDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SESSIONS_CONFIG_FILE = os.path.join(WORKDIR, "sessions.yml")


class SessionManagerRepository:

    def load_sessions(self) -> List[Dict[str, Any]]:
        """Load sessions from YAML file"""
        try:
            sessions = yaml.full_load(open(SESSIONS_CONFIG_FILE))
            return sessions
        except Exception:
            return []

    def save_session(self, session: Session) -> List[Dict[str, Any]]:
        sessions = self.load_sessions()
        sessions.append(session.to_dict())

        with open(SESSIONS_CONFIG_FILE, 'w') as f:
            yaml.dump(sessions, f, sort_keys=False)

        return sessions

    def delete_session(self, session: Session) -> List[Dict[str, Any]]:
        sessions = self.load_sessions()
        sessions.remove(session.to_dict())

        with open(SESSIONS_CONFIG_FILE, 'w') as f:
            yaml.dump(sessions, f, sort_keys=False)

        return sessions

    def session_from_dict(self, index: str, data: Dict[str, Any]) -> Session:
        engine = SessionEngine(data['engine']) if data.get('engine') else None

        # Convert configuration
        configuration: Optional[Union[CredentialsConfiguration, SourceConfiguration]] = None
        if data.get('configuration'):
            config_data = data['configuration']
            if engine in [SessionEngine.MYSQL, SessionEngine.MARIADB, SessionEngine.POSTGRESQL]:
                configuration = CredentialsConfiguration(**config_data)
            elif engine == SessionEngine.SQLITE:
                configuration = SourceConfiguration(**config_data)

        return Session(
            id=index,
            name=data['name'],
            engine=engine,
            configuration=configuration,
            comments=data.get('comments')
        )

    def session_to_dict(self, session: Session) -> Dict[str, Any]:
        """Convert Session object to dictionary"""
        return session.to_dict()
