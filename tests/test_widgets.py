"""Widget rendering, orientation handling and widget API endpoints."""

import io

from PIL import Image, ImageChops

from conftest import make_png


BLUE = (30, 120, 200)


def _bbox_of_difference(base, composed):
    """Bounding box of pixels that differ between two RGB images."""
    return ImageChops.difference(base, composed).getbbox()


def test_date_widget_font_scales_to_display(app_module):
    from widgets.date_widget import DateWidget
    widget = DateWidget({'enabled': True, 'position': {'preset': 'bottom_right'},
                         'style': {'style': 'classic'}})
    img = widget.render(800, 480)
    # Pillow's unscaled bitmap fallback yields ~28px tall widgets; a real
    # ~32px font with padding is comfortably taller and wider than that.
    assert img.height >= 40
    assert img.width >= 120


def test_widget_config_validation_and_persistence(client):
    assert client.get('/api/widgets/date').get_json()['enabled'] is False
    assert client.get('/api/widgets/nope').status_code == 404
    assert client.post('/api/widgets/nope', json={'enabled': True}).status_code == 404
    assert client.post('/api/widgets/date', json={'position': {'preset': 'middle'}}).status_code == 400
    assert client.post('/api/widgets/date', json={'style': {'style': 'neon'}}).status_code == 400
    assert client.post('/api/widgets/date', data='x', content_type='text/plain').status_code == 400

    resp = client.post('/api/widgets/date',
                       json={'enabled': 1, 'position': {'preset': 'top_left'},
                             'style': {'style': 'clean'}, 'junk': 'ignored'})
    assert resp.status_code == 200
    saved = client.get('/api/widgets/date').get_json()
    assert saved == {'enabled': True, 'position': {'preset': 'top_left'}, 'style': {'style': 'clean'}}
    listing = client.get('/api/widgets').get_json()
    assert listing['current']['date'] == saved
    assert 'date' in listing['available']


def test_widget_config_change_keeps_other_settings(client):
    client.post('/api/config', json={'orientation': 'portrait'})
    client.post('/api/widgets/date', json={'enabled': True})
    assert client.get('/api/config').get_json()['orientation'] == 'portrait'


def _enable_date_widget(client, preset='bottom_right'):
    resp = client.post('/api/widgets/date', json={'enabled': True, 'position': {'preset': preset}})
    assert resp.status_code == 200


def test_landscape_photo_gets_widget_bottom_right(client, app_module):
    (app_module.PHOTOS_DIR / 'land.png').write_bytes(make_png(800, 480, BLUE))
    _enable_date_widget(client)
    img = app_module.prepare_display_image(app_module.PHOTOS_DIR / 'land.png')
    assert img.size == (800, 480)
    bbox = _bbox_of_difference(Image.new('RGB', (800, 480), BLUE), img)
    assert bbox is not None
    left, top, right, bottom = bbox
    assert right - left > bottom - top          # text runs horizontally
    assert left > 400 and top > 240             # bottom-right quadrant


def test_portrait_photo_widget_is_rotated_with_photo(client, app_module):
    (app_module.PHOTOS_DIR / 'port.png').write_bytes(make_png(480, 800, BLUE))
    _enable_date_widget(client)
    img = app_module.prepare_display_image(app_module.PHOTOS_DIR / 'port.png')
    assert img.size == (800, 480)               # panel's native size
    bbox = _bbox_of_difference(Image.new('RGB', (800, 480), BLUE), img)
    assert bbox is not None
    left, top, right, bottom = bbox
    # Upright bottom-right on a 480x800 canvas lands top-right after the
    # 90° CCW rotation, with the text running vertically.
    assert bottom - top > right - left
    assert left > 400 and bottom < 240

    # The upright composition is what previews and the web UI show.
    upright, is_portrait = app_module.compose_photo(app_module.PHOTOS_DIR / 'port.png')
    assert is_portrait and upright.size == (480, 800)


def test_disabled_widget_leaves_photo_untouched(client, app_module):
    (app_module.PHOTOS_DIR / 'land.png').write_bytes(make_png(800, 480, BLUE))
    img = app_module.prepare_display_image(app_module.PHOTOS_DIR / 'land.png')
    assert _bbox_of_difference(Image.new('RGB', (800, 480), BLUE), img) is None


def test_preview_uses_submitted_config_without_saving(client, app_module, uploaded_photo):
    resp = client.post('/api/widgets/preview',
                       json={'photo': uploaded_photo,
                             'widgets': {'date': {'enabled': True, 'position': {'preset': 'top_left'},
                                                  'style': {'style': 'classic'}}}})
    assert resp.status_code == 200
    assert resp.get_json()['preview'].startswith('data:image/png;base64,')
    assert client.get('/api/widgets/date').get_json()['enabled'] is False

    assert client.post('/api/widgets/preview', json={'photo': 'missing.png'}).status_code == 404
    assert client.post('/api/widgets/preview', json={'widgets': []}).status_code == 400
    # No photo named: falls back to the newest photo
    assert client.post('/api/widgets/preview', json={}).status_code == 200


def test_preview_with_no_photos_is_404(client):
    assert client.post('/api/widgets/preview', json={}).status_code == 404


def test_serve_photo_with_widgets(client, uploaded_photo):
    resp = client.get(f'/photos/{uploaded_photo}/with-widgets')
    assert resp.status_code == 200
    assert resp.content_type == 'image/png'
    assert Image.open(io.BytesIO(resp.data)).size == (800, 480)
    assert client.get('/photos/missing.png/with-widgets').status_code == 404
