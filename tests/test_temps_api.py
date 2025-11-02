import os, json, sqlite3
import pytest
from flask import Flask
from gd.api import register_api

@pytest.fixture
def app(tmp_path):
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['GD_DB_PATH'] = str(tmp_path / 'app.db')
    register_api(app)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_temps_crud(client):
    # create
    res = client.post('/gd/api/temps', json={'first_name':'Jan','last_name':'Novák','hourly_rate':200})
    assert res.status_code == 201
    tid = res.get_json()['id']

    # list
    res = client.get('/gd/api/temps')
    assert res.status_code == 200
    rows = res.get_json()
    assert any(r['id']==tid for r in rows)

    # get
    res = client.get(f'/gd/api/temps/{tid}')
    assert res.status_code == 200
    row = res.get_json()
    assert row['first_name'] == 'Jan'

    # update
    res = client.put(f'/gd/api/temps/{tid}', json={'active': False, 'notes': 'jen víkendy'})
    assert res.status_code == 200

    # delete
    res = client.delete(f'/gd/api/temps/{tid}')
    assert res.status_code == 200

    # not found
    res = client.get(f'/gd/api/temps/{tid}')
    assert res.status_code == 404
