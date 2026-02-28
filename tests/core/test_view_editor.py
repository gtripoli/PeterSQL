import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from helpers.observables import Observable


class TestEditViewModel:
    """Test EditViewModel class for View Editor."""

    def test_init_creates_observables(self):
        """Test that EditViewModel initializes all required observables."""
        from windows.main.tabs.view import EditViewModel
        
        model = EditViewModel()
        
        assert isinstance(model.name, Observable)
        assert isinstance(model.schema, Observable)
        assert isinstance(model.definer, Observable)
        assert isinstance(model.sql_security, Observable)
        assert isinstance(model.algorithm, Observable)
        assert isinstance(model.constraint, Observable)
        assert isinstance(model.security_barrier, Observable)
        assert isinstance(model.force, Observable)
        assert isinstance(model.select_statement, Observable)

    def test_load_view_sets_name_observable(self):
        """Test that _load_view sets name observable from view."""
        from windows.main.tabs.view import EditViewModel
        
        model = EditViewModel()
        
        mock_view = Mock()
        mock_view.name = "test_view"
        mock_view.statement = "SELECT * FROM test"
        
        with patch('windows.main.tabs.view.CURRENT_SESSION') as mock_session:
            mock_session.get_value.return_value = None
            model._load_view(mock_view)
        
        assert model.name.get_value() == "test_view"
        assert model.select_statement.get_value() == "SELECT * FROM test"

    def test_update_view_sets_name_and_statement(self):
        """Test that update_view sets view name and statement from observables."""
        from windows.main.tabs.view import EditViewModel
        
        model = EditViewModel()
        
        mock_view = Mock()
        mock_view.name = ""
        mock_view.statement = ""
        
        with patch('windows.main.tabs.view.CURRENT_VIEW') as mock_current_view:
            mock_current_view.get_value.return_value = mock_view
            
            model.name.set_value("updated_view")
            model.select_statement.set_value("SELECT id FROM users")
            
            model.update_view(True)
        
        assert mock_view.name == "updated_view"
        assert mock_view.statement == "SELECT id FROM users"


class TestViewEditorController:
    """Test ViewEditorController class."""

    @pytest.fixture
    def mock_parent(self):
        """Create mock parent with all required UI elements."""
        parent = Mock()
        
        # Text controls
        parent.txt_view_name = Mock()
        parent.cho_view_schema = Mock()
        parent.cmb_view_definer = Mock()
        parent.cho_view_sql_security = Mock()
        parent.stc_view_select = Mock()
        
        # Radio buttons
        parent.rad_view_algorithm_undefined = Mock()
        parent.rad_view_algorithm_merge = Mock()
        parent.rad_view_algorithm_temptable = Mock()
        parent.rad_view_constraint_none = Mock()
        parent.rad_view_constraint_local = Mock()
        parent.rad_view_constraint_cascaded = Mock()
        parent.rad_view_constraint_check_only = Mock()
        parent.rad_view_constraint_read_only = Mock()
        
        # Checkboxes
        parent.chk_view_security_barrier = Mock()
        parent.chk_view_force = Mock()
        
        # Buttons
        parent.btn_save_view = Mock()
        parent.btn_delete_view = Mock()
        parent.btn_cancel_view = Mock()
        
        # Panels
        parent.pnl_view_editor_root = Mock()
        parent.panel_views = Mock()
        parent.m_notebook7 = Mock()
        
        return parent

    def test_init_binds_controls(self, mock_parent):
        """Test that controller initializes and binds controls."""
        from windows.main.tabs.view import ViewEditorController
        
        with patch('windows.main.tabs.view.CURRENT_VIEW') as mock_current_view:
            with patch('windows.main.tabs.view.wx_call_after_debounce'):
                controller = ViewEditorController(mock_parent)
                
                assert controller.parent == mock_parent
                assert controller.model is not None
                assert mock_current_view.subscribe.call_count == 2

    def test_get_original_view_returns_none_for_new_view(self, mock_parent):
        """Test that _get_original_view returns None for new views."""
        from windows.main.tabs.view import ViewEditorController
        
        with patch('windows.main.tabs.view.CURRENT_VIEW'):
            with patch('windows.main.tabs.view.wx_call_after_debounce'):
                controller = ViewEditorController(mock_parent)
                
                mock_view = Mock()
                type(mock_view).is_new = PropertyMock(return_value=True)
                
                result = controller._get_original_view(mock_view)
                assert result is None

    def test_has_changes_returns_true_for_new_view(self, mock_parent):
        """Test that _has_changes returns True for new views."""
        from windows.main.tabs.view import ViewEditorController
        
        with patch('windows.main.tabs.view.CURRENT_VIEW'):
            with patch('windows.main.tabs.view.wx_call_after_debounce'):
                controller = ViewEditorController(mock_parent)
                
                mock_view = Mock()
                type(mock_view).is_new = PropertyMock(return_value=True)
                
                result = controller._has_changes(mock_view)
                assert result is True

    def test_update_button_states_disables_all_when_no_view(self, mock_parent):
        """Test that update_button_states disables all buttons when no view."""
        from windows.main.tabs.view import ViewEditorController
        
        with patch('windows.main.tabs.view.CURRENT_VIEW') as mock_current_view:
            with patch('windows.main.tabs.view.wx_call_after_debounce'):
                mock_current_view.get_value.return_value = None
                
                controller = ViewEditorController(mock_parent)
                controller.update_button_states()
                
                mock_parent.btn_save_view.Enable.assert_called_with(False)
                mock_parent.btn_cancel_view.Enable.assert_called_with(False)
                mock_parent.btn_delete_view.Enable.assert_called_with(False)

    def test_update_button_states_enables_save_cancel_for_new_view(self, mock_parent):
        """Test that update_button_states enables save/cancel for new views."""
        from windows.main.tabs.view import ViewEditorController
        
        with patch('windows.main.tabs.view.CURRENT_VIEW') as mock_current_view:
            with patch('windows.main.tabs.view.wx_call_after_debounce'):
                mock_view = Mock()
                type(mock_view).is_new = PropertyMock(return_value=True)
                mock_current_view.get_value.return_value = mock_view
                
                controller = ViewEditorController(mock_parent)
                controller.update_button_states()
                
                mock_parent.btn_save_view.Enable.assert_called_with(True)
                mock_parent.btn_cancel_view.Enable.assert_called_with(True)
                mock_parent.btn_delete_view.Enable.assert_called_with(False)


class TestSQLViewSaveMethod:
    """Test SQLView save method and database refresh."""

    def test_save_calls_create_for_new_view(self):
        """Test that save() calls create() for new views."""
        from structures.engines.database import SQLView
        
        mock_view = Mock()
        type(mock_view).is_new = PropertyMock(return_value=True)
        mock_view.create = Mock(return_value=True)
        mock_view.alter = Mock()
        mock_database = Mock()
        mock_database.refresh = Mock()
        mock_view.database = mock_database
        
        result = SQLView.save(mock_view)
        
        mock_view.create.assert_called_once()
        mock_view.alter.assert_not_called()
        mock_database.refresh.assert_called_once()
        assert result is True

    def test_save_calls_alter_for_existing_view(self):
        """Test that save() calls alter() for existing views."""
        from structures.engines.database import SQLView
        
        mock_view = Mock()
        type(mock_view).is_new = PropertyMock(return_value=False)
        mock_view.create = Mock()
        mock_view.alter = Mock(return_value=True)
        mock_database = Mock()
        mock_database.refresh = Mock()
        mock_view.database = mock_database
        
        result = SQLView.save(mock_view)
        
        mock_view.create.assert_not_called()
        mock_view.alter.assert_called_once()
        mock_database.refresh.assert_called_once()
        assert result is True

    def test_save_refreshes_database_after_success(self):
        """Test that save() refreshes database after successful save."""
        from structures.engines.database import SQLView
        
        mock_view = Mock()
        type(mock_view).is_new = PropertyMock(return_value=True)
        mock_view.create = Mock(return_value=True)
        mock_database = Mock()
        mock_database.refresh = Mock()
        mock_view.database = mock_database
        
        SQLView.save(mock_view)
        
        mock_database.refresh.assert_called_once()
