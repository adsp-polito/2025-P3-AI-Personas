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
    '/api/surveys',
    '/api/surveys/{survey_id}',
    '/api/groups',
    '/api/groups/countries',
    '/api/groups/{group_id}',
    '/api/surveys/{survey_id}/simulate',
    '/api/surveys/{survey_id}/responses',
    '/api/surveys/{survey_id}/statistics',
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


def test_schema_exposes_swagger_servers(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv('ADSP_API_HOST', raising=False)
    monkeypatch.delenv('ADSP_API_PORT', raising=False)
    monkeypatch.delenv('ADSP_API_DOCS_SERVER_SCHEME', raising=False)
    monkeypatch.delenv('ADSP_API_DOCS_SERVER_HOST', raising=False)
    monkeypatch.delenv('ADSP_API_DOCS_SERVER_BASE_PATH', raising=False)

    schema = _schema()
    servers = schema.get('servers', [])
    assert isinstance(servers, list)
    assert len(servers) >= 2

    assert servers[0]['url'] == '/'
    assert servers[1]['url'] == '{scheme}://{host}{base_path}'

    variables = servers[1].get('variables', {})
    assert variables['scheme']['default'] == 'http'
    assert variables['host']['default'] == 'localhost:8000'
    assert variables['base_path']['default'] == ''


def test_schema_uses_env_defaults_for_swagger_server(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv('ADSP_API_HOST', '0.0.0.0')
    monkeypatch.setenv('ADSP_API_PORT', '9000')
    monkeypatch.setenv('ADSP_API_DOCS_SERVER_SCHEME', 'https')
    monkeypatch.delenv('ADSP_API_DOCS_SERVER_HOST', raising=False)
    monkeypatch.setenv('ADSP_API_DOCS_SERVER_BASE_PATH', 'gateway/api')

    schema = _build_app().openapi()
    servers = schema['servers']
    variables = servers[1]['variables']

    assert variables['scheme']['default'] == 'https'
    assert variables['host']['default'] == 'localhost:9000'
    assert variables['base_path']['default'] == '/gateway/api'


def test_survey_and_group_paths_expose_get_and_post():
    paths = _paths()

    assert 'get' in paths['/api/surveys']
    assert 'post' in paths['/api/surveys']

    assert 'get' in paths['/api/groups']
    assert 'post' in paths['/api/groups']

    assert 'get' in paths['/api/surveys/{survey_id}/statistics']
