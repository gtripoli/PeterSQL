import pytest

from structures.session import Session
from structures.engines.database import SQLDatabase


class BaseProcedureTests:
    
    def get_procedure_statement(self) -> str:
        raise NotImplementedError
    
    def get_procedure_parameters(self) -> str:
        return ""
    
    def test_procedure_create_and_drop(self, session: Session, database: SQLDatabase):
        procedure = session.context.build_empty_procedure(
            database,
            name="test_procedure",
            parameters=self.get_procedure_parameters(),
            statement=self.get_procedure_statement()
        )
        
        assert procedure.is_new is True
        
        result = procedure.create()
        assert result is True
        
        database.procedures.refresh()
        found = any(p.name == "test_procedure" for p in database.procedures.get_value())
        assert found is True
        
        result = procedure.drop()
        assert result is True
        
        database.procedures.refresh()
        found = any(p.name == "test_procedure" for p in database.procedures.get_value())
        assert found is False
