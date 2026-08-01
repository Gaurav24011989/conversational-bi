import pytest

from app.execution.guardrails import enforce_table_allowlist, validate_sql_query


class TestSQLGuardrails:
    def test_valid_select(self):
        ok, msg = validate_sql_query("SELECT id, name FROM users WHERE active = true")
        assert ok is True
        assert msg == ""

    def test_valid_with_cte(self):
        ok, msg = validate_sql_query("WITH cte AS (SELECT 1) SELECT * FROM cte")
        assert ok is True

    def test_blocks_insert(self):
        ok, msg = validate_sql_query("INSERT INTO users VALUES (1, 'a')")
        assert ok is False
        assert "SELECT" in msg or "blocked" in msg.lower()

    def test_blocks_drop(self):
        ok, msg = validate_sql_query("DROP TABLE users")
        assert ok is False

    def test_blocks_multi_statement(self):
        ok, msg = validate_sql_query("SELECT 1; SELECT 2")
        assert ok is False

    def test_table_allowlist_pass(self):
        ok, msg = enforce_table_allowlist("SELECT * FROM orders", ["orders", "customers"])
        assert ok is True

    def test_table_allowlist_fail(self):
        ok, msg = enforce_table_allowlist("SELECT * FROM secrets", ["orders"])
        assert ok is False

    def test_table_allowlist_none(self):
        ok, msg = enforce_table_allowlist("SELECT * FROM anything", None)
        assert ok is True
