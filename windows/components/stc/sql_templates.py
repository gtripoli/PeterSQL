from typing import Optional

from structures.engines.database import SQLDatabase, SQLTable


class SQLTemplate:
    def __init__(self, name: str, template: str, description: str = ""):
        self.name = name
        self.template = template
        self.description = description
    
    def render(
        self, 
        database: Optional[SQLDatabase] = None, 
        table: Optional[SQLTable] = None
    ) -> str:
        text = self.template
        
        if table:
            text = text.replace("{table}", table.name)
            if table.columns:
                columns = ", ".join(col.name for col in table.columns[:5])
                text = text.replace("{columns}", columns)
        else:
            text = text.replace("{table}", "table_name")
            text = text.replace("{columns}", "column1, column2")
        
        text = text.replace("{condition}", "condition")
        text = text.replace("{values}", "value1, value2")
        
        return text


SQL_TEMPLATES = [
    SQLTemplate(
        name="SELECT *",
        template="SELECT * FROM {table}",
        description="Select all columns from table"
    ),
    SQLTemplate(
        name="SELECT with WHERE",
        template="SELECT {columns}\nFROM {table}\nWHERE {condition}",
        description="Select specific columns with condition"
    ),
    SQLTemplate(
        name="INSERT",
        template="INSERT INTO {table} ({columns})\nVALUES ({values})",
        description="Insert new row"
    ),
    SQLTemplate(
        name="UPDATE",
        template="UPDATE {table}\nSET column = value\nWHERE {condition}",
        description="Update rows"
    ),
    SQLTemplate(
        name="DELETE",
        template="DELETE FROM {table}\nWHERE {condition}",
        description="Delete rows"
    ),
    SQLTemplate(
        name="SELECT with JOIN",
        template="SELECT t1.*, t2.*\nFROM {table} t1\nJOIN table2 t2 ON t1.id = t2.id",
        description="Select with JOIN"
    ),
    SQLTemplate(
        name="SELECT with GROUP BY",
        template="SELECT {columns}, COUNT(*)\nFROM {table}\nGROUP BY {columns}",
        description="Select with grouping"
    ),
    SQLTemplate(
        name="CREATE TABLE",
        template="CREATE TABLE {table} (\n    id INTEGER PRIMARY KEY,\n    name TEXT NOT NULL\n)",
        description="Create new table"
    ),
]
