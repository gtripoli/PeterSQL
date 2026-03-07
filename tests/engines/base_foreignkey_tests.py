import pytest


class BaseForeignKeyTests:
    
    def test_foreignkey_create_and_drop(self, session, database, create_users_table):
        users_table = create_users_table(database, session)
        
        posts_table = session.context.build_empty_table(database, name="posts")
        
        id_column = session.context.build_empty_column(
            posts_table,
            self.get_datatype_class().INTEGER,
            name="id",
            is_auto_increment=True,
            is_nullable=False,
        )
        
        user_id_column = session.context.build_empty_column(
            posts_table,
            self.get_datatype_class().INTEGER,
            name="user_id",
            is_nullable=False,
        )
        
        posts_table.columns.append(id_column)
        posts_table.columns.append(user_id_column)
        
        primary_index = session.context.build_empty_index(
            posts_table,
            self.get_indextype_class().PRIMARY,
            ["id"],
            name=self.get_primary_key_name(),
        )
        posts_table.indexes.append(primary_index)
        
        posts_table.create()
        database.tables.refresh()
        posts_table = next(t for t in database.tables.get_value() if t.name == "posts")
        
        fk = session.context.build_empty_foreign_key(
            posts_table,
            ["user_id"],
            name="fk_posts_users",
        )
        fk.reference_table = "users"
        fk.reference_columns = ["id"]
        fk.on_delete = "CASCADE"
        fk.on_update = "CASCADE"
        
        assert fk.create() is True
        
        posts_table.foreign_keys.refresh()
        foreign_keys = posts_table.foreign_keys.get_value()
        assert len(foreign_keys) > 0, f"No foreign keys found. Expected fk_posts_users"
        assert any(fk.name == "fk_posts_users" for fk in foreign_keys), f"Foreign key fk_posts_users not found. Found: {[fk.name for fk in foreign_keys]}"
        
        created_fk = next((fk for fk in foreign_keys if fk.name == "fk_posts_users"), None)
        assert created_fk is not None
        assert created_fk.drop() is True
        
        posts_table.foreign_keys.refresh()
        foreign_keys = posts_table.foreign_keys.get_value()
        assert not any(fk.name == "fk_posts_users" for fk in foreign_keys)
        
        posts_table.drop()
        users_table.drop()

    def get_datatype_class(self):
        raise NotImplementedError("Subclasses must implement get_datatype_class()")

    def get_indextype_class(self):
        raise NotImplementedError("Subclasses must implement get_indextype_class()")

    def get_primary_key_name(self) -> str:
        raise NotImplementedError("Subclasses must implement get_primary_key_name()")
