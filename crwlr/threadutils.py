import base64
import html
import json

from bson import Binary
from bson.binary import BINARY_SUBTYPE

from crwlr.linkextractor import retrieve_links, async_extractor
from crwlr.textmanipulator import TextManipulator


def new_thread(thread: dict) -> dict:
    return {'_id': thread['no'],
            'ts': __ts(thread),
            'active': True,
            '#replies': thread['replies'],
            '#images': thread['images'],
            'unique_ips': 0,
            'posts': [],
            'users': {},
            'kw': [],
            'link_kw': [],
            'polarity': 0.0,
            'subjectivity': 0.0,
            'newreps': 0}


def update_thread(thread: dict, fetched_thread: dict) -> tuple[dict, dict]:
    thread_ops = {'#replies': fetched_thread['replies'], '#images': fetched_thread['images']}
    thread.update(thread_ops)
    return thread, thread_ops


async def fetch_posts(thread: dict, thread_api: str, txtmpl: TextManipulator,
                thread_ops: dict, flags=True) -> tuple[dict, dict, dict, dict, dict, list[str, ...]]:
    posts, new_usrs, attachments, stats = {}, [], {}, {'new_posts': 0, 'words': 0}
    if flags:
        stats['flags'] = {'B': {}, 'C': {}}
    t = json.loads(thread_api)
    total_posts = len(t['posts'])
    nfetched = len(thread['posts'])
    if 'closed' in t['posts'][0].keys():
        newreps = 0
        thread['active'] = False
        thread_ops['active'] = False
    else:
        newreps = total_posts - nfetched
        thread['unique_ips'] = t['posts'][0]['unique_ips']
        thread_ops['unique_ips'] = t['posts'][0]['unique_ips']
    thread['newreps'] = newreps
    thread_ops['newreps'] = newreps
    ops = {'poffset': nfetched, 'thread': thread_ops, 'update': {'posts': {}, 'users': {}}}
    for n in range(nfetched, total_posts):
        posts, new_usrs, thread, attachments, ops_psts_usrs = __process_post(t['posts'][n], n, nfetched, thread, posts,
                                                                             new_usrs, attachments, txtmpl, flags)
        ops['update'] = __append_dict(ops['update'], ops_psts_usrs)
        words = thread['posts'][n]['wc']
        stats['words'] += words
        if flags:
            ft, flg = thread['posts'][n]['flag'].split(':')
            if ft != 'X':
                if flg not in stats['flags'][ft].keys():
                    stats['flags'][ft][flg] = {'posts': 1, 'words': words}
                else:
                    stats['flags'][ft][flg]['posts'] += 1
                    stats['flags'][ft][flg]['words'] += words
    thread['link_kw'] = await async_extractor(txtmpl, [html.unescape(link) for post in thread['posts'][nfetched:]
                                                       for link in post['links'] if link[-4:] not in
                                                       ['.pdf', '.jpg', '.png', '.svg', '.bmp', '.mp3', '.mp4']])
    clean_msgs = [txtmpl.prep_grammar(html.unescape(((p['title'] + ' ') if p['title'] != '' else '') +
                                                    (p['msg'] if p['wc'] > 5 else '')))
                  for p in thread['posts'][nfetched:]]
    stats['new_posts'] = len(thread['posts']) - nfetched
    return posts, attachments, thread, stats, ops, clean_msgs


def __process_post(p: dict, n: int, prev_fetched_posts: int,
                   thread: dict, posts: dict, new_usrs: list[str, ...],
                   attachments: dict, tm: TextManipulator, flags) -> tuple[dict, list[str,...], dict, dict, dict]:
    pnum, tposts = p['no'], thread['posts']
    ttl = tm.remove_tags(p['sub']) if 'sub' in p.keys() else ''
    if 'com' in p.keys() and len(p['com']) > 0:
        reptos, links, message, wordcount = __process_message(p['com'], tm)
        reptoposts = __find_posts_by_pnums(reptos, tposts) if len(reptos) > 0 else []
        reptousrs = list(set(tposts[pn]['userid'] for pn in reptoposts))
    else:
        reptoposts, reptousrs, links = [], [], []
        wordcount = 0
        message = ''
    post = {'_id': pnum,
            'ts': __ts(p),
            'userid': p['id'] if 'id' in p.keys() else 'unknown',
            'title': ttl,
            'msg': message,
            'wc': wordcount,
            'links': links,
            'rby_posts': [],
            'rby_users': [],
            'polarity': 0.0,
            'subjectivity': 0.0}
    if flags:
        post['flag'] = 'C:' + p['country'] if ('country' in p.keys()) else (
            'B:' + p['board_flag'] if 'board_flag' in p.keys() else 'X:XX')
    if n > 0:

        post['rto_posts'] = reptoposts
        post['rto_users'] = reptousrs
        post['delta'] = float(__ts(p) - tposts[-1]['ts']) / 1000.0,
        post['repmin'] = round(float(n) / (float(__ts(p) - tposts[0]['ts']) / 60000.0),7)
    if 'ext' in p.keys():
        post['attachment'], attachments = __process_attachment(p, attachments)
    else:
        post['attachment'] = b''
    userid = post['userid']
    op_dict = {'posts': {}, 'users': {'update': {}}}
    if len(reptoposts) > 0:
        for idx in reptoposts:
            tposts[idx]['rby_posts'].append(n)
            rtuid = tposts[idx]['userid']
            if userid not in thread['users'][rtuid]['rby'] and userid != rtuid:
                thread['users'][rtuid]['rby'].append(userid)
                if rtuid not in new_usrs:
                    op_dict['users']['update'][rtuid] = {'rby': [userid]}
            if idx < prev_fetched_posts:
                op_dict['posts'][idx] = {'rby_posts': [n]}
    thread['posts'].append(post)
    posts[pnum] = {'_id': pnum, 'tn': thread['_id'], 'n': n, 'active': thread['active'], 'ts': post['ts']}
    thread, new_usrs, ops_user = __process_user(post['userid'], new_usrs, n, post['flag'] if flags else '', reptousrs, thread)
    op_dict['users'] = __append_dict(op_dict['users'], ops_user)
    return posts, new_usrs, thread, attachments, op_dict


def __process_attachment(p: dict, attachments: dict) -> tuple[bytes, dict]:
    bytemd5 = bytes.fromhex(base64.b64decode(p['md5']).hex())
    if bytemd5 in attachments.keys():
        attachments[bytemd5]['posts'].append(p['no'])
    else:
        attachments[bytemd5] = {'_id': Binary(bytemd5, subtype=BINARY_SUBTYPE),
                                'md5': p['md5'],
                                'filename': p['filename'],
                                'size': p['fsize'],
                                'ext': p['ext'],
                                'posts': [p['no']]}
        #  svdfp = len(p['filename']) == 9 and p['filename'].isnumeric() and int(p['filename'][0]) <=
    return bytemd5, attachments


def __process_user(userid: str, new_usrs: list[str, ...], n: int,
                   flag: str, rtusers: list[str, ...], thread: dict) -> tuple[dict, list[str,...],dict]:
    if userid not in thread['users'].keys():
        thread['users'][userid] = {'flag': flag,
                                   'op': False if n > 0 else True,
                                   'posts': [n],
                                   'rto': rtusers,
                                   'rby': []}
        new_usrs.append(userid)
        return thread, new_usrs, {}
    else:
        thread['users'][userid]['posts'].append(n)
        if userid not in new_usrs:
            op_dict = {userid: {'posts': [n], 'rto': []}}
            for rtu in rtusers:
                if rtu not in thread['users'][userid]['rto']:
                    thread['users'][userid]['rto'].append(rtu)
                    op_dict[userid]['rto'].append(rtu)
            if len(op_dict[userid]['rto']) < 1:
                del op_dict[userid]['rto']
            if thread['users'][userid]['flag'].startswith('BF:') and flag.startswith('CF:'):
                thread['users'][userid]['flag'] = flag
                op_dict[userid]['flag'] = flag
            return thread, new_usrs, op_dict
        for rtu in rtusers:
            if rtu not in thread['users'][userid]['rto']:
                thread['users'][userid]['rto'].append(rtu)
        if thread['users'][userid]['flag'].startswith('BF:') and flag.startswith('CF:'):
            thread['users'][userid]['flag'] = flag
        return thread, new_usrs, {}


def __append_dict(basedict: dict, d: dict) -> dict:
    for k, v in d.items():
        if k not in basedict.keys() or k == 'flag':
            basedict[k] = v
        elif isinstance(basedict[k], dict) and isinstance(v, dict):
            basedict[k] = __append_dict(basedict[k], v)
        else:
            basedict[k].extend(v)
    return basedict


def __process_message(msg: str, tm: TextManipulator) -> tuple[tuple[int,...], tuple[str,...], str, int]:
    reptos, message = tm.extract_replied_posts(tm.remove_tags(msg))
    links = retrieve_links(message, tm)
    message2 = tm.replace_links(message)
    return tuple(reptos), links, tm.safe_escape(message2), tm.word_count(message2)


def __ts(post: dict) -> int:
    if 'tim' in post.keys():
        return post['tim']
    return post['time'] * 1000


def __find_posts_by_pnums(pnums: tuple, posts: list) -> list[int, ...]:
    pnums = sorted(pnums)
    idx = 0
    postindices = []
    for i, v in enumerate(posts):
        if v['_id'] == pnums[idx]:
            postindices.append(i)
            idx += 1
            if idx == len(pnums):
                return postindices
    return postindices



"""
def process_thread(t: dict, threads: dict, thread_api_url: str, textmanipulator: TextManipulator, flags=True) -> [dict, dict, dict]:
    tnum = t['no']
    thread_ops = {}
    stats = {'new_posts': 0, 'new_threads': 0, 'words': 0}
    if flags:
        stats['flags'] = {'B': {}, 'C': {}}
    if tnum not in threads.keys():
        threads[tnum] = {'#': tnum,
                         'ts': t['tim'],
                         'active': True,
                         '#replies': t['replies'],
                         '#images': t['images'],
                         'unique_ips': 0,
                         'posts': [],
                         'users': {},
                         'rank': {}}
        stats['new_threads'] = 1
    elif t['replies'] > threads[tnum]['#replies']:
        thread_ops = {'#replies': t['replies'], '#images': t['images']}
        threads[tnum].update(thread_ops)
    else:
        return {'poffset': -1}, {}, {}
    total_posts = len(threads[tnum]['posts'])
    thread_api = __check_thread(thread_api_url)
    if thread_api != '':
        thread = json.loads(thread_api)
        num_fetched_posts = len(threads[tnum]['posts'])
        if 'closed' in thread['posts'][0].keys():
            threads[tnum]['active'] = False
            thread_ops['active'] = False
        else:
            threads[tnum]['unique_ips'] = thread['posts'][0]['unique_ips']
            thread_ops['unique_ips'] = thread['posts'][0]['unique_ips']
        op_dict_thread = {'poffset': num_fetched_posts, 'thread': thread_ops, 'update': {'posts': {}, 'users': {}}}
        for i, p in enumerate(thread['posts'][num_fetched_posts:]):
            pnum_offset = i + num_fetched_posts
            op_dict_posts_users = __process_post(p, pnum_offset, threads[tnum], textmanipulator, flags)
            op_dict_thread['update'] = __append_dict(op_dict_thread['update'], op_dict_posts_users)
            words = threads[tnum]['posts'][pnum_offset]['wordcount']
            stats['words'] += words
            if flags:
                ft, flg = threads[tnum]['posts'][pnum_offset]['flag'].split(':')
                if flg not in stats['flags'][ft].keys():
                    stats['flags'][ft][flg] = {'posts': 1, 'words': words}
                else:
                    stats['flags'][ft][flg]['posts'] += 1
                    stats['flags'][ft][flg]['words'] += words
        stats['new_posts'] = len(threads[tnum]['posts']) - total_posts
        return op_dict_thread, threads[tnum], stats
    else:
        threads[tnum]['active'] = False
        return {'poffset': -2, 'thread': thread_ops}, threads[tnum], {}


"""
