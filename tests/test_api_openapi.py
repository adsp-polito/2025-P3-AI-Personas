"""OpenAPI contract checks for the public REST API surface."""

import pytest as pytest


fastapi = pytest.importorskip('fastapi')
unused_fastapi = fastapi


API_PATHS = [
    '/' 'health',
    '/v1/auth/register',
    '/v1/auth/validate',
    '/v1/personas',
    '/v1/personas/{persona_id}/profile',
    '/v1/personas/{persona_id}/system-prompt',
    '/v1/' 'chat',
    '/v1/ingestion/upload',
    '/v1/reports/{persona_id}',
]


def _build_app():
    from adsp.app.api_server import create_app

    return create_app()


def _schema() -> dict:
    app = _build_app()
    schema = app.openapi()
    assert isinstance(schema, dict)
    return schema


def _paths() -> dict:
    schema = _schema()
    paths = schema.get('paths', {})
    assert isinstance(paths, dict)
    return paths


def test_schema_has_paths_block():
    schema = _schema()
    assert 'paths' in schema
    assert isinstance(schema['paths'], dict)


def test_paths_include_required_endpoints():
    paths = _paths()
    required = set(API_PATHS)
    assert required.issubset(set(paths.keys()))


def test_paths_include_core_endpoints():
    paths = _paths()
    assert '/health' in paths
    assert '/v1/chat' in paths
    assert '/v1/personas' in paths


def test_paths_use_string_keys():
    paths = _paths()
    for path in paths:
        assert isinstance(path, str)
        assert path.startswith('/')


def test_path_items_are_mappings():
    paths = _paths()
    for path, item in paths.items():
        assert isinstance(path, str)
        assert isinstance(item, dict)


def test_schema_has_info_block():
    schema = _schema()
    info = schema.get('info', {})
    assert isinstance(info, dict)
    assert isinstance(info.get('title'), str)
    assert isinstance(info.get('version'), str)


def test_schema_has_openapi_version():
    schema = _schema()
    assert isinstance(schema.get('openapi'), str)
