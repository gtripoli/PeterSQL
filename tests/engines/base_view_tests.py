import pytest


class BaseViewSaveTests:
    
    def test_save_creates_new_view_and_refreshes_database(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="test_save_view",
            statement=self.get_view_statement(),
        )
        
        assert view.is_new is True
        
        result = view.save()
        
        assert result is True
        database.views.refresh()
        views = database.views.get_value()
        assert any(v.name == "test_save_view" for v in views)
        
        view.drop()

    def test_save_alters_existing_view_and_refreshes_database(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="test_alter_view",
            statement=self.get_simple_view_statement(),
        )
        view.create()
        
        database.views.refresh()
        views = database.views.get_value()
        created_view = next((v for v in views if v.name == "test_alter_view"), None)
        assert created_view is not None
        
        created_view.statement = self.get_updated_view_statement()
        
        result = created_view.save()
        
        assert result is True
        database.views.refresh()
        views = database.views.get_value()
        updated_view = next((v for v in views if v.name == "test_alter_view"), None)
        assert updated_view is not None
        
        created_view.drop()

    def get_view_statement(self) -> str:
        raise NotImplementedError("Subclasses must implement get_view_statement()")

    def get_simple_view_statement(self) -> str:
        raise NotImplementedError("Subclasses must implement get_simple_view_statement()")

    def get_updated_view_statement(self) -> str:
        raise NotImplementedError("Subclasses must implement get_updated_view_statement()")


class BaseViewIsNewTests:
    
    def test_is_new_returns_true_for_new_view(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="new_view",
            statement=self.get_simple_view_statement(),
        )
        
        assert view.is_new is True

    def test_is_new_returns_false_for_existing_view(self, session, database):
        view = session.context.build_empty_view(
            database,
            name="existing_view",
            statement=self.get_simple_view_statement(),
        )
        view.create()
        
        database.views.refresh()
        views = database.views.get_value()
        existing_view = next((v for v in views if v.name == "existing_view"), None)
        
        assert existing_view is not None
        assert existing_view.is_new is False
        
        existing_view.drop()

    def get_simple_view_statement(self) -> str:
        raise NotImplementedError("Subclasses must implement get_simple_view_statement()")


class BaseViewDefinerTests:
    
    def test_get_definers_returns_list(self, session):
        definers = session.context.get_definers()
        
        assert isinstance(definers, list)
        assert len(definers) > 0
        assert all('@' in definer for definer in definers)
