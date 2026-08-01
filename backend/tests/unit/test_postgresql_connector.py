import pytest

from app.connectors.postgresql import PostgreSQLConnector


class TestPostgreSQLValidator:
    def setup_method(self):
        self.connector = PostgreSQLConnector()

    def test_valid_select(self):
        result = self.connector.validate_query("SELECT * FROM users LIMIT 10")
        assert result.valid is True

    def test_blocks_delete(self):
        result = self.connector.validate_query("DELETE FROM users")
        assert result.valid is False

    def test_blocks_update(self):
        result = self.connector.validate_query("UPDATE users SET name = 'x'")
        assert result.valid is False
