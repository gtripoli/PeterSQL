import os
import tempfile
import pytest
import yaml

from structures.connection import Connection, ConnectionEngine, ConnectionDirectory
from structures.configurations import CredentialsConfiguration, SourceConfiguration, SSHTunnelConfiguration
from windows.connections.repository import ConnectionsRepository


class TestConnectionsRepository:
    @pytest.fixture
    def temp_yaml(self):
        """Create a temporary YAML file path for testing."""
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.yml', delete=False) as tmp:
            tmp_path = tmp.name
        yield tmp_path
        os.unlink(tmp_path)

    @pytest.fixture
    def repo(self, temp_yaml, monkeypatch):
        """Create a ConnectionsRepository instance with a temporary YAML file."""
        return ConnectionsRepository(config_file=str(temp_yaml))

    def test_load_empty_yaml(self, temp_yaml, repo):
        """Test loading from an empty or non-existent YAML file."""
        # Ensure file doesn't exist or is empty
        with open(temp_yaml, 'w') as f:
            f.write("")

        connections = repo.load()
        assert connections == []

    def test_load_connections_from_yaml(self, temp_yaml, repo):
        """Test loading connections from YAML."""
        data = [
            {
                'id': 1,
                'name': 'Test SQLite',
                'engine': 'SQLite',
                'configuration': {'filename': ':memory:'},
                'comments': 'Test connection'
            },
            {
                'id': 2,
                'name': 'Test MySQL',
                'engine': 'MySQL',
                'configuration': {
                    'hostname': 'localhost',
                    'port': 3306,
                    'username': 'user',
                    'password': 'pass'
                },
                'ssh_tunnel': {
                    'enabled': True,
                    'hostname': 'remote.host',
                    'port': 22,
                    'username': 'sshuser',
                    'password': 'sshpass',
                    'local_port': 3307
                }
            }
        ]
        with open(temp_yaml, 'w') as f:
            yaml.dump(data, f)

        connections = repo.load()
        assert len(connections) == 2

        # Check first connection
        conn1 = connections[0]
        assert conn1.id == 1
        assert conn1.name == 'Test SQLite'
        assert conn1.engine == ConnectionEngine.SQLITE
        assert isinstance(conn1.configuration, SourceConfiguration)
        assert conn1.configuration.filename == ':memory:'
        assert conn1.comments == 'Test connection'

        # Check second connection
        conn2 = connections[1]
        assert conn2.id == 2
        assert conn2.name == 'Test MySQL'
        assert conn2.engine == ConnectionEngine.MYSQL
        assert isinstance(conn2.configuration, CredentialsConfiguration)
        assert conn2.configuration.hostname == 'localhost'
        assert conn2.configuration.port == 3306
        assert conn2.configuration.username == 'user'
        assert conn2.configuration.password == 'pass'
        assert conn2.ssh_tunnel.enabled is True
        assert conn2.ssh_tunnel.hostname == 'remote.host'

    def test_load_directories_from_yaml(self, temp_yaml, repo):
        """Test loading directories with nested connections."""
        data = [
            {
                'type': 'directory',
                'name': 'Production',
                'children': [
                    {
                        'id': 1,
                        'name': 'Prod DB',
                        'engine': 'PostgreSQL',
                        'configuration': {
                            'hostname': 'prod.example.com',
                            'port': 5432,
                            'username': 'produser',
                            'password': 'prodpass'
                        }
                    }
                ]
            },
            {
                'type': 'directory',
                'name': 'Development',
                'children': [
                    {
                        'id': 2,
                        'name': 'Dev DB',
                        'engine': 'SQLite',
                        'configuration': {'filename': 'dev.db'}
                    }
                ]
            }
        ]
        with open(temp_yaml, 'w') as f:
            yaml.dump(data, f)

        items = repo.load()
        assert len(items) == 2

        # Check first directory
        dir1 = items[0]
        assert isinstance(dir1, ConnectionDirectory)
        assert dir1.name == 'Production'
        assert len(dir1.children) == 1

        conn = dir1.children[0]
        assert conn.name == 'Prod DB'
        assert conn.engine == ConnectionEngine.POSTGRESQL

        # Check second directory
        dir2 = items[1]
        assert isinstance(dir2, ConnectionDirectory)
        assert dir2.name == 'Development'
        assert len(dir2.children) == 1

        conn2 = dir2.children[0]
        assert conn2.name == 'Dev DB'
        assert conn2.engine == ConnectionEngine.SQLITE

    def test_add_connection(self, temp_yaml, repo):
        """Test adding a new connection."""
        config = SourceConfiguration(filename='test.db')
        connection = Connection(
            id=0,
            name='New Connection',
            engine=ConnectionEngine.SQLITE,
            configuration=config,
            comments='Added connection'
        )
        conn_id = repo.add_connection(connection)
        assert conn_id == 0

        # Check YAML
        with open(temp_yaml, 'r') as f:
            data = yaml.safe_load(f)
        assert len(data) == 1
        assert data[0]['name'] == 'New Connection'
        assert data[0]['id'] == 0

    def test_save_connection(self, temp_yaml, repo):
        """Test saving/updating an existing connection."""
        # Start with a connection
        data = [{
            'id': 1,
            'name': 'Original Name',
            'engine': 'SQLite',
            'configuration': {'filename': ':memory:'}
        }]
        with open(temp_yaml, 'w') as f:
            yaml.dump(data, f)

        # Load and modify
        connections = repo.load()
        conn = connections[0]
        conn.name = 'Updated Name'

        # Save
        repo.save_connection(conn)

        # Check YAML was updated
        with open(temp_yaml, 'r') as f:
            updated_data = yaml.safe_load(f)
        assert updated_data[0]['name'] == 'Updated Name'

    def test_delete_connection(self, temp_yaml, repo):
        """Test deleting a connection."""
        # Start with connections
        data = [
            {'id': 1, 'name': 'Conn1', 'engine': 'SQLite', 'configuration': {'filename': 'db1.db'}},
            {'id': 2, 'name': 'Conn2', 'engine': 'SQLite', 'configuration': {'filename': 'db2.db'}}
        ]
        with open(temp_yaml, 'w') as f:
            yaml.dump(data, f)

        # Load and delete first connection
        connections = repo.load()
        conn_to_delete = connections[0]
        repo.delete_connection(conn_to_delete)

        # Check only one connection remains
        with open(temp_yaml, 'r') as f:
            updated_data = yaml.safe_load(f)
        assert len(updated_data) == 1
        assert updated_data[0]['name'] == 'Conn2'

    def test_add_directory(self, temp_yaml, repo):
        """Test adding a new directory."""
        with open(temp_yaml, 'w') as f:
            f.write("[]")

        directory = ConnectionDirectory(name='New Directory')

        repo.add_directory(directory)

        # Check YAML
        with open(temp_yaml, 'r') as f:
            data = yaml.safe_load(f)
        assert len(data) == 1
        assert data[0]['type'] == 'directory'
        assert data[0]['name'] == 'New Directory'

    def test_delete_directory(self, temp_yaml, repo):
        """Test deleting a directory."""
        data = [
            {'type': 'directory', 'name': 'Dir1', 'children': []},
            {'type': 'directory', 'name': 'Dir2', 'children': []}
        ]
        with open(temp_yaml, 'w') as f:
            yaml.dump(data, f)

        # Load and delete first directory
        items = repo.load()
        dir_to_delete = items[0]
        repo.delete_directory(dir_to_delete)

        # Check only one directory remains
        with open(temp_yaml, 'r') as f:
            updated_data = yaml.safe_load(f)
        assert len(updated_data) == 1
        assert updated_data[0]['name'] == 'Dir2'
