"""Configuration endpoint and cycle-thread settings behaviour."""


def test_defaults_when_no_config_file(client):
    data = client.get('/api/config').get_json()
    assert data['cycle_enabled'] is False
    assert data['cycle_interval'] == 3600
    assert data['orientation'] == 'landscape'
    assert data['photo_order'] == []


def test_post_config_persists_and_clamps_interval(client, app_module):
    resp = client.post('/api/config', json={'cycle_interval': 5, 'orientation': 'portrait'})
    assert resp.status_code == 200
    assert resp.get_json()['cycle_interval'] == 60  # minimum is one minute
    assert app_module.CONFIG_FILE.exists()
    assert client.get('/api/config').get_json()['orientation'] == 'portrait'


def test_post_config_rejects_bad_values(client):
    assert client.post('/api/config', json={'orientation': 'diagonal'}).status_code == 400
    assert client.post('/api/config', json={'cycle_interval': 'soon'}).status_code == 400
    assert client.post('/api/config', json={'photo_order': 'a.png'}).status_code == 400
    assert client.post('/api/config', data='not json', content_type='text/plain').status_code == 400


def test_photo_order_is_sanitised(client):
    resp = client.post('/api/config', json={'photo_order': ['../x.png', 'ok.png']})
    assert resp.get_json()['photo_order'] == ['x.png', 'ok.png']


def test_cycle_settings_change_wakes_cycle_thread(client, app_module):
    app_module.settings_changed.clear()
    client.post('/api/config', json={'orientation': 'portrait'})
    assert not app_module.settings_changed.is_set()
    client.post('/api/config', json={'cycle_interval': 120})
    assert app_module.settings_changed.is_set()


def test_update_config_preserves_other_keys(app_module):
    app_module.update_config(orientation='portrait')
    app_module.update_config(current_photo='a.png')
    config = app_module.load_config()
    assert config['orientation'] == 'portrait'
    assert config['current_photo'] == 'a.png'


def test_corrupt_config_file_falls_back_to_defaults(app_module, client):
    app_module.CONFIG_FILE.write_text('{not json')
    assert client.get('/api/config').get_json()['cycle_interval'] == 3600
