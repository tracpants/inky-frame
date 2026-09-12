"""Upload, crop, list, delete, display and preview endpoints."""

import base64
import io

from conftest import make_png


def test_index_renders(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'Inky Frame' in resp.data


def test_upload_stores_original_and_display_copy(client, app_module, uploaded_photo):
    assert uploaded_photo.startswith('holiday_') and uploaded_photo.endswith('.png')
    assert (app_module.PHOTOS_DIR / uploaded_photo).is_file()
    assert (app_module.ORIGINALS_DIR / uploaded_photo).is_file()
    listed = client.get('/api/photos').get_json()
    assert [p['name'] for p in listed] == [uploaded_photo]


def test_upload_requires_file(client):
    assert client.post('/api/photos/upload', data={}).status_code == 400


def test_upload_rejects_non_image_extension(client, app_module):
    resp = client.post(
        '/api/photos/upload',
        data={'file': (io.BytesIO(b'MZ...'), 'tool.exe')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 400
    assert not any(app_module.ORIGINALS_DIR.iterdir())


def test_upload_rejects_non_image_content(client, app_module):
    resp = client.post(
        '/api/photos/upload',
        data={'file': (io.BytesIO(b'definitely not a png'), 'fake.png')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 400
    assert not any(app_module.PHOTOS_DIR.iterdir())


def _data_url(png):
    return 'data:image/png;base64,' + base64.b64encode(png).decode()


def test_upload_cropped_new_photo(client, app_module):
    resp = client.post('/api/photos/upload-cropped',
                       json={'image': _data_url(make_png(800, 480)), 'filename': 'beach.jpg'})
    assert resp.status_code == 200
    name = resp.get_json()['name']
    assert name.startswith('beach_') and name.endswith('.png')
    assert (app_module.PHOTOS_DIR / name).is_file()


def test_upload_cropped_recrop_overwrites_existing(client, app_module, uploaded_photo):
    before = (app_module.PHOTOS_DIR / uploaded_photo).read_bytes()
    resp = client.post('/api/photos/upload-cropped',
                       json={'image': _data_url(make_png(480, 800, (1, 2, 3))),
                             'filename': uploaded_photo, 'is_recrop': True})
    assert resp.status_code == 200
    assert resp.get_json()['name'] == uploaded_photo
    assert (app_module.PHOTOS_DIR / uploaded_photo).read_bytes() != before


def test_upload_cropped_recrop_cannot_escape_photos_dir(client, app_module):
    resp = client.post('/api/photos/upload-cropped',
                       json={'image': _data_url(make_png(10, 10)),
                             'filename': '../escaped.png', 'is_recrop': True})
    assert resp.status_code == 404
    assert not (app_module.DATA_DIR / 'escaped.png').exists()
    assert not (app_module.PHOTOS_DIR / 'escaped.png').exists()


def test_upload_cropped_recrop_of_missing_photo_is_404(client):
    resp = client.post('/api/photos/upload-cropped',
                       json={'image': _data_url(make_png(10, 10)),
                             'filename': 'ghost.png', 'is_recrop': True})
    assert resp.status_code == 404


def test_upload_cropped_rejects_bad_payloads(client):
    assert client.post('/api/photos/upload-cropped', json={}).status_code == 400
    assert client.post('/api/photos/upload-cropped',
                       json={'image': 'data:image/png;base64,@@@'}).status_code == 400
    garbage = base64.b64encode(b'not an image').decode()
    assert client.post('/api/photos/upload-cropped',
                       json={'image': garbage}).status_code == 400


def test_delete_removes_both_copies(client, app_module, uploaded_photo):
    assert client.delete(f'/api/photos/{uploaded_photo}').status_code == 200
    assert not (app_module.PHOTOS_DIR / uploaded_photo).exists()
    assert not (app_module.ORIGINALS_DIR / uploaded_photo).exists()
    assert client.delete(f'/api/photos/{uploaded_photo}').status_code == 404


def test_serve_photo_and_original(client, uploaded_photo, png_bytes):
    assert client.get(f'/photos/{uploaded_photo}').data == png_bytes
    assert client.get(f'/api/photos/original/{uploaded_photo}').data == png_bytes
    assert client.get('/photos/nope.png').status_code == 404


def test_preview_returns_thumbnail(client, uploaded_photo):
    data = client.get(f'/api/preview/{uploaded_photo}').get_json()
    assert data['thumbnail'].startswith('data:image/png;base64,')
    assert client.get('/api/preview/nope.png').status_code == 404


def test_display_without_hardware_reports_dev_mode(client, app_module, uploaded_photo):
    resp = client.post(f'/api/display/{uploaded_photo}')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['displayed'] == uploaded_photo
    assert body['success'] is False  # no inky library in the test environment
    assert app_module.load_config()['current_photo'] == uploaded_photo
    assert client.post('/api/display/missing.png').status_code == 404
