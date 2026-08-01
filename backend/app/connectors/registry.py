from app.connectors.base import DataSourceConnector
from app.connectors.elasticsearch import ElasticsearchConnector
from app.connectors.mongodb import MongoDBConnector
from app.connectors.mysql import MySQLConnector
from app.connectors.postgresql import PostgreSQLConnector
from app.models import DataSourceType

_CONNECTORS: dict[str, DataSourceConnector] = {
    DataSourceType.POSTGRESQL.value: PostgreSQLConnector(),
    DataSourceType.MYSQL.value: MySQLConnector(),
    DataSourceType.MONGODB.value: MongoDBConnector(),
    DataSourceType.ELASTICSEARCH.value: ElasticsearchConnector(),
}


def get_connector(dialect: str) -> DataSourceConnector:
    connector = _CONNECTORS.get(dialect)
    if connector is None:
        raise ValueError(f"Unsupported data source type: {dialect}")
    return connector
