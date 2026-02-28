import pytest


class BaseSSHTunnelTests:
    
    def test_get_version_through_ssh_tunnel(self, ssh_session):
        version = ssh_session.context.get_server_version()
        
        assert version is not None
        assert isinstance(version, str)
        assert len(version) > 0
