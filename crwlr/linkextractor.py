import asyncio
import re
from ssl import SSLError
import httpx
import lxml.html as lxhtml
from httpx._exceptions import *
from lxml.etree import ParserError

from crwlr.textmanipulator import TextManipulator


def retrieve_links(txt: str, tm: TextManipulator) -> tuple:
    links, count = [], 0
    for m in re.finditer(tm.rgx_lnk2, txt):
        m1 = m.group()
        if m1.find('https') > 0:
            m1 = m1[m1.find('https'):]
        elif m1.find('http') > 0:
            m1 = m1[m1.find('http'):]
        m1.replace('\n', '')
        if len(links) > 0 and ((m1[:4] in ('.org', '.net', '.com', '.gov')) or
                               (m1[:3] in ('.de', '.ch', '.at', '.me', '.co', '.nz', '.uk'))):
            links[count - 1] = f'{links[count - 1]}{m1}'
        else:
            s = m1.split('.')
            if len(s) == 2 and s[0].isalpha() and s[1].isalpha():
                continue
            links.append(remove_googleamp(m1))
            count += 1
    return tuple(links)


# def extractor(links: [tuple[str, ...], list[str, ...]], tm: TextManipulator) -> list:
#     keywords = []
#     if len(links) > 0:
#         for link in links:
#             twitter = False
#             if link.startswith('https://www.google.com/amp/s/'):
#                 link = __remove_googleamp(link)
#             elif bool(re.search(tm.rgx_twttr, link)):
#                 link = re.sub(tm.rgx_twttr, r'\1\3', link)
#                 twitter = True
#             try:
#                 check = requests.head(link, timeout=3, allow_redirects=True)
#                 if 'text/html' in check.headers['content-type']:
#                     response = requests.get(link, timeout=2.1)
#                     doc = lxhtml.document_fromstring(response.text.encode())
#                     keywords.append(__get_meta_description(doc, tm))
#                     if not twitter:
#                         keywords.extend(__get_article_content(doc))
#             except requests.exceptions.RequestException as e:
#                 print(e)
#     keywords = [tm.prep_grammar(tm.clean_text(k0, rm_links=True, rm_replytos=False)) for k0 in tuple(set(keywords))]
#     return list(set(keywords))


async def async_extractor(tm: TextManipulator, links: [str, ...]) -> list:
    if len(links) < 1:
        return []
    keywords = []
    loop = asyncio.get_running_loop()
    tasks = [loop.create_task(__async_extract_link(link, tm)) for link in links]
    coroutines = asyncio.as_completed(tasks)
    for coro in coroutines:
        result = await coro
        keywords.extend(result)
    keywords = [tm.prep_grammar(tm.clean_text(k0, rm_tags=True, rm_links=True, rm_replytos=False, escape=False))
                for k0 in tuple(set(keywords)) if k0 is not None and isinstance(k0, str)]
    return list(set(keywords))


async def __async_extract_link(link, tm):
    keywords = []
    twitter = False
    if link.startswith('https://www.google.com/amp/s/'):
        link = __remove_googleamp(link)
    elif bool(re.search(tm.rgx_twttr, link)):
        link = re.sub(tm.rgx_twttr, r'\1\3', link)
        twitter = True
    if not link.startswith('http'):
        if 'wikipedia.org' not in link:
            return keywords
        link = 'http://' + link
    else:
        link = link.replace('https://', 'http://')
    try:
        async with httpx.AsyncClient(verify=False) as session:
            check = await session.get(link, timeout=1.9)
            if 'content-type' in check.headers and 'text/html' in check.headers['content-type']:
                response = await session.get(link, timeout=1.9)
                doc = lxhtml.document_fromstring(response.text.encode())
                keywords.append(__get_meta_description(doc, tm))
                if not twitter:
                    keywords.extend(__get_article_content(doc))
    except (ConnectError, TimeoutError, HTTPError, HTTPStatusError, ConnectionError, ConnectionResetError,
            ConnectTimeout, ConnectionRefusedError, ConnectionAbortedError, InvalidURL, NetworkError, ParserError,
            RequestError, TimeoutException, TransportError, TooManyRedirects, CloseError, KeyError, ValueError,
            TypeError, SSLError) as e:
        if str(e) not in ('', ' ', 'Document is empty', '[Errno -2] Name or service not known'):
            print(f"|{e}|", link)
    return keywords


def __get_article_content(doc):
    keywords = []
    article_content = doc.xpath("//*[contains(@itemprop, 'articleBody')]")
    if len(article_content) > 0:
        article_content = article_content[0].text_content().strip()
        keywords.append(article_content)
        desc = doc.xpath("//*[contains(@itemprop, 'description')]")
        if len(desc) > 0:
            desc = desc[0].text_content().strip()
            keywords.append(desc)
    else:
        article_content = doc.xpath("//*[contains(@class, 'entry-content')]")
        if len(article_content) > 0:
            article_content = article_content[0].text_content().strip()
            keywords.append(article_content)
        else:
            article_content = doc.xpath(
                "//*[(contains(@class, 'article') and contains(@class, 'content')) or (contains(@class, 'article') and contains(@class, 'text'))]")
            if len(article_content) > 0:
                article_content = article_content[0].text_content().strip()
                keywords.append(article_content)
            else:
                article_content = doc.xpath("//article")
                if len(article_content) > 0:
                    article_content = article_content[0].text_content().strip()
                    keywords.append(article_content)
    return keywords


def __get_meta_description(doc, tm: TextManipulator):
    meta_description = doc.xpath("//meta[contains(@property, 'description')]/@content")
    if len(meta_description) > 0:
        meta_description = re.sub(tm.rgx_meta, r'\4', meta_description[0])
        #print(meta_description)
        return meta_description


def remove_googleamp(link: str) -> str:
    idx = link.find('google.com/amp/s/')
    if idx > -1:
        return __remove_googleamp(link, idx=idx+17)
    return link


def __remove_googleamp(link: str, idx=29) -> str:
    link = link[idx:]  # len('https://www.google.com/amp/s/'):]
    return link[:-4] if link.endswith('amp/') else link