import json

import pytest

from app.connectors.elasticsearch import ElasticsearchConnector


class TestElasticsearchValidator:
    def setup_method(self):
        self.connector = ElasticsearchConnector()

    def test_valid_search_query(self):
        query = json.dumps({
            "index": "orders-*",
            "body": {"query": {"match_all": {}}, "size": 10},
        })
        result = self.connector.validate_query(query)
        assert result.valid is True

    def test_valid_aggregation_query(self):
        query = json.dumps({
            "index": "logs-2025",
            "body": {
                "size": 0,
                "aggs": {
                    "by_status": {"terms": {"field": "status.keyword"}}
                },
            },
        })
        result = self.connector.validate_query(query)
        assert result.valid is True

    def test_missing_index(self):
        query = json.dumps({"body": {"query": {"match_all": {}}}})
        result = self.connector.validate_query(query)
        assert result.valid is False
        assert "index" in result.message

    def test_missing_body(self):
        query = json.dumps({"index": "orders"})
        result = self.connector.validate_query(query)
        assert result.valid is False
        assert "body" in result.message

    def test_blocks_script(self):
        query = json.dumps({
            "index": "orders",
            "body": {"script": {"source": "ctx._source.field = 'x'"}},
        })
        result = self.connector.validate_query(query)
        assert result.valid is False

    def test_invalid_json(self):
        result = self.connector.validate_query("not json")
        assert result.valid is False


class TestElasticsearchAggregationFlattening:
    def setup_method(self):
        self.connector = ElasticsearchConnector()

    def test_flatten_terms_buckets(self):
        aggs = {
            "by_status": {
                "buckets": [
                    {"key": "success", "doc_count": 100},
                    {"key": "error", "doc_count": 5},
                ]
            }
        }
        rows = self.connector._flatten_aggregations(aggs)
        assert len(rows) == 2
        assert rows[0]["by_status"] == "success"
        assert rows[0]["by_status_doc_count"] == 100

    def test_flatten_metric_value(self):
        aggs = {"total_revenue": {"value": 12345.67}}
        rows = self.connector._flatten_aggregations(aggs)
        assert rows == [{"total_revenue": 12345.67}]
