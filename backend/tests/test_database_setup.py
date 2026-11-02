from sqlalchemy import inspect


def test_test_database_contains_required_tables(test_engine):
    inspector = inspect(test_engine)
    tables = set(inspector.get_table_names())

    required_tables = {
        "companies",
        "users",
        "admin_activation_tokens",
    }

    assert required_tables.issubset(tables)