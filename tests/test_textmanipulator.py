from crwlr.textmanipulator import TextManipulator


def test_clean_text():
    text1 = '{}'
    text2 = '[]'
    text3 = ':'
    text4 = ';'
    text5 = '*'
    text6 = '|'
    text7 = '\\'
    text8 = 'text'
    text9 = '{[:;*|\\text\\|*;:]}'
    assert TextManipulator().clean_text(text1, rm_tags=False, rm_replytos=False, rm_links=False, rm_utm=False, escape=True, length=-1) == ''
    assert TextManipulator().clean_text(text2, rm_tags=False, rm_replytos=False, rm_links=False, rm_utm=False, escape=True, length=-1) == ''
    assert TextManipulator().clean_text(text3, rm_tags=False, rm_replytos=False, rm_links=False, rm_utm=False, escape=True, length=-1) == ''
    assert TextManipulator().clean_text(text4, rm_tags=False, rm_replytos=False, rm_links=False, rm_utm=False, escape=True, length=-1) == ''
    assert TextManipulator().clean_text(text5, rm_tags=False, rm_replytos=False, rm_links=False, rm_utm=False, escape=True, length=-1) == ''
    assert TextManipulator().clean_text(text6, rm_tags=False, rm_replytos=False, rm_links=False, rm_utm=False, escape=True, length=-1) == ''
    assert TextManipulator().clean_text(text7, rm_tags=False, rm_replytos=False, rm_links=False, rm_utm=False, escape=True, length=-1) == '\\'
    assert TextManipulator().clean_text(text8, rm_tags=False, rm_replytos=False, rm_links=False, rm_utm=False, escape=True, length=-1) == 'text'
    assert TextManipulator().clean_text(text9, rm_tags=False, rm_replytos=False, rm_links=False, rm_utm=False, escape=True, length=-1) == '\\text\\'

    text10 = '<wbr><em></em></span><span class="quote"><br><p></p></blockquote>'
    assert TextManipulator().clean_text(text10, rm_tags=True, rm_replytos=False, rm_links=False, rm_utm=False, escape=False, length=-1) == '\n\n\n'

    text11 = '?utm=test_utm_line_text'
    text12 = ''
    assert TextManipulator().clean_text(text11, rm_tags=False, rm_replytos=False, rm_links=False, rm_utm=True, escape=False, length=-1) == ''
    assert TextManipulator().clean_text(text12, rm_tags=False, rm_replytos=False, rm_links=False, rm_utm=True, escape=False, length=-1) == ''

    text13 = 'textone'
    text14 = 'text longer than 10 characters'
    assert TextManipulator().clean_text(text13, rm_tags=False, rm_replytos=False, rm_links=False, rm_utm=False, escape=False, length=0) == 'textone'
    assert TextManipulator().clean_text(text14, rm_tags=False, rm_replytos=False, rm_links=False, rm_utm=False, escape=False, length=25) == 'text longer than 10'


def test_truncate_ws():
    text1 = '1 whitespace'
    text2 = '2  whitespaces'
    text3 = '3   whitespaces'
    text4 = '4    whitespaces'
    textmorethan256 = 'x  x   x    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx    x   x  x'
    assert TextManipulator().truncate_ws(text1) == '1 whitespace'
    assert TextManipulator().truncate_ws(text2) == '2 whitespaces'
    assert TextManipulator().truncate_ws(text3) == '3 whitespaces'
    assert TextManipulator().truncate_ws(text4) == '4 whitespaces'
    assert TextManipulator().truncate_ws(textmorethan256) == 'x x x xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx x x x'


def test_replace_links():
    text1 = 'https://www.youtube.com/'
    text2 = 'test text https://it.wikipedia.org/wiki/Meccanica_quantistica test text'
    text3 = 'https://www.icorsi.ch/my/'
    assert TextManipulator().replace_links(text1) == '[youtube]'
    assert TextManipulator().replace_links(text2) == 'test text [link] test text'
    assert TextManipulator().replace_links(text3) == '[link]'


# def test_prep_grammar():
#     text1 = '\n test text one'
#     text2 = '10%'
#     text3 = '[youtube] test text two'
#     text4 = '[link] test text three'
#     text5 = 'i\'m he\'s she\'s it\'s you\'ll he\'ll she\'ll it\'ll we\'ll they\'ll you\'d he\'d she\'d it\'d we\'d they\'d you\'re we\'re they\'re you\'ve we\'ve they\'ve 1234567890k lel kek lol like fuck shit kys tbh aa wtf lmao lmfao pls link eh muh omfg omg btfo lulz btw anon anons test text four'
#     assert TextManipulator().prep_grammar(text1) == 'test text one'
#     assert TextManipulator().prep_grammar(text2) == '10 percent'
#     assert TextManipulator().prep_grammar(text3) == 'test text two'
#     assert TextManipulator().prep_grammar(text4) == 'test text three'
#     assert TextManipulator().prep_grammar(text5) == '1234567890k test text four'


def test_word_count():
    text1 = 'test string [youtube] [link] { } [ ]  ( ) - = ` ~ + " : ; \' ? > < ! @ # $ % ^ & * some other word'
    assert TextManipulator().word_count(text1) == 5
