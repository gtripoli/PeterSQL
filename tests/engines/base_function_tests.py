import pytest

from structures.session import Session
from structures.engines.database import SQLDatabase


class BaseFunctionTests:
    
    def get_function_statement(self) -> str:
        raise NotImplementedError
    
    def get_function_parameters(self) -> str:
        return "x integer"
    
    def get_function_returns(self) -> str:
        return "integer"

    def get_updated_function_statement(self) -> str:
        return self.get_function_statement()
    
    def test_function_create_and_drop(self, session: Session, database: SQLDatabase):
        function = session.context.build_empty_function(
            database,
            name="test_function",
            parameters=self.get_function_parameters(),
            returns=self.get_function_returns(),
            statement=self.get_function_statement()
        )
        
        assert function.is_new is True
        
        result = function.create()
        assert result is True
        
        database.functions.refresh()
        found = any(f.name == "test_function" for f in database.functions.get_value())
        assert found is True
        
        result = function.drop()
        assert result is True
        
        database.functions.refresh()
        found = any(f.name == "test_function" for f in database.functions.get_value())
        assert found is False

    def test_function_alter(self, session: Session, database: SQLDatabase):
        function = session.context.build_empty_function(
            database,
            name="test_function_alter",
            parameters=self.get_function_parameters(),
            returns=self.get_function_returns(),
            statement=self.get_function_statement(),
        )

        assert function.create() is True

        database.functions.refresh()
        found = any(
            f.name == "test_function_alter" for f in database.functions.get_value()
        )
        assert found is True

        function.statement = self.get_updated_function_statement()
        assert function.alter() is True

        database.functions.refresh()
        found = any(
            f.name == "test_function_alter" for f in database.functions.get_value()
        )
        assert found is True

        assert function.drop() is True
