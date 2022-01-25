from crwlr.linkextractor import *


def test_retrieve_link():
    assert retrieve_links(txt='test str https://www.google.ch/?hl=it', tm=TextManipulator()) == ('https://www.google.ch/?hl=it',)
    assert retrieve_links(txt='test str https://www.google.ch/?hl=it, https://www.icorsi.ch/my/, https://www.icorsi.ch/', tm=TextManipulator()) == ('https://www.google.ch/?hl=it', 'https://www.icorsi.ch/my/', 'https://www.icorsi.ch/')


def test_async_extractor():
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(async_extractor(tm=TextManipulator(), links=['https://it.wikipedia.org/wiki/Spin', 'https://it.wikipedia.org/wiki/Meccanica_quantistica']))
    loop.close()
    assert res == []

