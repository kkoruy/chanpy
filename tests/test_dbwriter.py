from db.flaskdbwriter import FlaskDBWriter
from flask import Flask

app = Flask(__name__)
writer = FlaskDBWriter(app)


def test_create_thread():
    thread = {
        '_id': 1,
        'users': 'name',
        'title': 'title',
        'posts': [],
        'text': 'text'
    }

    assert writer.create_thread(thread) == thread


def test_create_post():
    post = {
        '_id': 2,
        'users': 'name',
        'title': 'title',
        'text': 'text',
        'thread_id': 1
    }

    assert writer.post_on_thread(post)['posts'][0] == post


def test_delete_thread():
    assert writer.delete_thread(1) == 'True'
