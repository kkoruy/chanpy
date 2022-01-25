from crwlr.threadutils import *
from crwlr.threadutils import __ts


def test_new_thread():
    thread = {'no': 1,
              'time': 164000,
              'replies': 0,
              'images': 0}

    assert new_thread(thread) == {'_id': 1,
                                  'ts': __ts(thread),
                                  'active': True,
                                  '#replies': 0,
                                  '#images': 0,
                                  'unique_ips': 0,
                                  'posts': [],
                                  'users': {},
                                  'kw': [],
                                  'link_kw': [],
                                  'polarity': 0.0,
                                  'subjectivity': 0.0,
                                  'newreps': 0}


def test_update_thread():
    fetched = {
        'no': 1,
        'time': 164000,
        'replies': 10,
        'images': 10
    }
    thread = {
         '_id': 1,
         'ts': 164000 * 1000,
         'active': True,
         '#replies': 0,
         '#images': 0,
         'unique_ips': 0,
         'posts': [],
         'users': {},
         'kw': [],
         'link_kw': [],
         'polarity': 0.0,
         'subjectivity': 0.0,
         'newreps': 0
    }

    assert update_thread(thread, fetched) == (
        {
            '_id': 1,
            'ts': 164000 * 1000,
            'active': True,
            '#replies': 10,
            '#images': 10,
            'unique_ips': 0,
            'posts': [],
            'users': {},
            'kw': [],
            'link_kw': [],
            'polarity': 0.0,
            'subjectivity': 0.0,
            'newreps': 0
        },
        {
            '#replies': fetched['replies'],
            '#images': fetched['images']
        }
    )

