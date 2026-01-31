#!/usr/bin/env python3

import os
import tempfile
import yaml


from structures.connection import Connection, ConnectionEngine, ConnectionDirectory
from structures.configurations import SourceConfiguration
from windows.connections.repository import ConnectionsRepository

def test_repository():
    # Create a temporary YAML file
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.yml', delete=False) as f:
        temp_yaml = f.name

    try:
        # Monkey patch the config file path
        import windows.connections.repository
        original_config = windows.connections.repository.CONNECTIONS_CONFIG_FILE
        windows.connections.repository.CONNECTIONS_CONFIG_FILE = temp_yaml

        repo = ConnectionsRepository()

        # Test 1: Load from empty file
        print("Test 1: Loading from empty YAML...")
        connections = repo.load()
        assert connections == [], f"Expected empty list, got {connections}"
        print("✓ Passed")

        # Test 2: Add a connection
        print("Test 2: Adding a connection...")
        config = SourceConfiguration(filename='test.db')
        connection = Connection(
            id=0,
            name='Test Connection',
            engine=ConnectionEngine.SQLITE,
            configuration=config,
            comments='Test comment'
        )
        conn_id = repo.add_connection(connection)
        print(f"✓ Added connection with ID: {conn_id}")

        # Test 3: Verify YAML was written
        print("Test 3: Verifying YAML write...")
        with open(temp_yaml, 'r') as f:
            data = yaml.safe_load(f)
        assert len(data) == 1, f"Expected 1 item, got {len(data)}"
        assert data[0]['name'] == 'Test Connection', f"Name mismatch: {data[0]['name']}"
        print("✓ YAML correctly written")

        # Test 4: Add a directory
        print("Test 4: Adding a directory...")
        directory = ConnectionDirectory(name='Test Directory')
        repo.add_directory(directory)
        print("✓ Directory added")

        # Test 5: Verify directory in YAML
        print("Test 5: Verifying directory in YAML...")
        with open(temp_yaml, 'r') as f:
            data = yaml.safe_load(f)
        assert len(data) == 2, f"Expected 2 items, got {len(data)}"
        directory_data = [item for item in data if item.get('type') == 'directory']
        assert len(directory_data) == 1, f"Expected 1 directory, got {len(directory_data)}"
        assert directory_data[0]['name'] == 'Test Directory', f"Directory name mismatch: {directory_data[0]['name']}"
        print("✓ Directory correctly written")

        # Test 6: Load and verify
        print("Test 6: Loading and verifying data...")
        items = repo.load()
        assert len(items) == 2, f"Expected 2 items, got {len(items)}"
        # One connection, one directory
        connections_loaded = [item for item in items if isinstance(item, Connection)]
        directories_loaded = [item for item in items if isinstance(item, ConnectionDirectory)]
        assert len(connections_loaded) == 1, f"Expected 1 connection, got {len(connections_loaded)}"
        assert len(directories_loaded) == 1, f"Expected 1 directory, got {len(directories_loaded)}"
        assert connections_loaded[0].name == 'Test Connection'
        assert directories_loaded[0].name == 'Test Directory'
        print("✓ Data correctly loaded")

        print("\nAll tests passed! ✅")

    finally:
        # Restore original config
        windows.connections.repository.CONNECTIONS_CONFIG_FILE = original_config
        # Clean up temp file
        if os.path.exists(temp_yaml):
            os.unlink(temp_yaml)

if __name__ == '__main__':
    test_repository()
