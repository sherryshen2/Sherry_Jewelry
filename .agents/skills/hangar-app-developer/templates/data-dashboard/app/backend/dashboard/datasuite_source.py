import json
import os
from collections.abc import Iterable, Mapping
from typing import Any

from .models import SourceDataset
from .normalize import source_rows

REQUIRED_SECRETS = (
    "DATASUITE_APP_KEY",
    "DATASUITE_APP_SECRET",
    "DATASUITE_SYSTEM_NAME",
    "DATASUITE_END_USER",
)


def configured_secrets() -> dict[str, str]:
    return {key: os.getenv(key, "").strip() for key in REQUIRED_SECRETS}


def _record(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {"value": value}


def read_datasuite(
    *,
    api_name: str,
    version: str,
    scope: Iterable[str],
    parameters: Mapping[str, Any],
    enable_cache: bool = True,
) -> SourceDataset:
    """Execute the Datasuite OLAP query and materialize every returned shard."""
    # Keep this optional import inside the enabled source path. CSV and Sheets must
    # remain usable if a local developer has not installed the Datasuite SDK yet.
    from dataservice.body import Body, Expressions
    from dataservice.query_configuration import QueryConfiguration
    from dataservice.sdk import Client

    secrets = configured_secrets()
    missing = [key for key, value in secrets.items() if not value]
    if missing:
        raise ValueError(f"Missing Datasuite secrets: {', '.join(missing)}")
    if not api_name.strip() or not version.strip():
        raise ValueError("Datasuite API name and version are required")

    expressions = Expressions()
    for parameter_name, value in parameters.items():
        expression_value = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        expressions.addExpression(parameterName=str(parameter_name), value=expression_value)

    client = (
        Client()
        .create()
        .appKey(secrets["DATASUITE_APP_KEY"])
        .appSecret(secrets["DATASUITE_APP_SECRET"])
        .scope([item for item in scope if item])
        .systemName(secrets["DATASUITE_SYSTEM_NAME"])
        .endUser(secrets["DATASUITE_END_USER"])
        .refresh()
    )
    request_body = Body(expressions=expressions.getExpressions()).__dict__
    query_config = QueryConfiguration(
        apiName=api_name.strip(),
        version=version.strip(),
        enableCache=enable_cache,
        queryPattern=QueryConfiguration.QueryPattern.OLAP,
        requestBody=request_body,
        network=QueryConfiguration.Env.INTRANET,
    )

    rows: list[dict[str, Any]] = []
    for shard in client.callWithQueryConfig(query_config):
        for row in shard:
            rows.append(_record(row))
    source_name = "Datasuite"
    normalized_rows, columns = source_rows(rows, source_name)
    return SourceDataset(name=source_name, source_type="datasuite", rows=normalized_rows, columns=columns)
