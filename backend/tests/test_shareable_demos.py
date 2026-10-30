import json
import pytest

from fastapi.testclient import TestClient

from app.db import Database
from app.main import create_app
from tools.prepare_shareable_demos import prepare_shareable_demos


def test_six_exported_packages_have_expected_committed_decisions_and_no_private_keys(tmp_path):
    database = tmp_path / 'demo.sqlite3'
    output = tmp_path / 'kit'
    catalog = prepare_shareable_demos(database, output)
    assert len(catalog) == 6
    assert len({item['file_name'] for item in catalog}) == 6
    with TestClient(create_app(Database(database))) as client:
        for item in catalog:
            folder = output / item['id']
            assert {path.name for path in folder.iterdir()} == {item['file_name'], 'manifest.json', 'signature.txt'}
            response = client.post('/api/verify', data={
                'manifest': (folder / 'manifest.json').read_text(),
                'signature': (folder / 'signature.txt').read_text()},
                files={'file': (item['file_name'], (folder / item['file_name']).read_bytes())})
            assert response.status_code == 200
            result = response.json()
            assert (result['status'], result['reason_code']) == (item['expected_status'], item['expected_reason'])
            audit = client.get('/api/audit', params={'verification_id': result['verification_id']}).json()
            assert any(event['event_type'] == 'VERIFICATION_DECIDED' for event in audit)
        assert len(client.get('/api/verifications').json()) == 6
    public_key = json.loads((output / 'public-key.json').read_text())
    assert set(public_key) == {'key_id', 'laboratory_id', 'public_key_base64'}
    for path in output.rglob('*'):
        if path.is_file():
            assert b'PRIVATE KEY' not in path.read_bytes()
            assert path.suffix not in {'.pem', '.key'}


def test_sender_refuses_to_overwrite_an_existing_kit(tmp_path):
    database = tmp_path / 'demo.sqlite3'
    output = tmp_path / 'kit'
    prepare_shareable_demos(database, output)
    snapshot = {path.relative_to(output): path.read_bytes() for path in output.rglob('*') if path.is_file()}
    database_before = database.read_bytes()
    with pytest.raises(FileExistsError, match='fresh output directory'):
        prepare_shareable_demos(database, output)
    assert database.read_bytes() == database_before
    assert {path.relative_to(output): path.read_bytes() for path in output.rglob('*') if path.is_file()} == snapshot
