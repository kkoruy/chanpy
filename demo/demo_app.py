from chanpy.chanpy import Client


def print_users():
    print('Users that have an account:')
    print(client.users())


def print_images():
    print('\nNumber of images present in DB: {0}'.format(client.n_images()))


def print_replies():
    print('\nNumber of replies present in DB: {0}'.format(client.n_replies()))


def print_max_attach():
    print('Name: {0}\nSize: {1} MB\nExtension: {2}'.format(client.max_att()[0], client.max_att()[1], client.max_att()[2]))


def print_all_attach():
    print('\033[4m[<filename>, <size (MB)>, <extension>]\033[0m\n')
    print(client.att())


def print_latest_n_posts(n):
    if n > 1:
        print('\033[4m[<thread number>, <active?>, <relative date (H)>]\033[0m\n')
        print(client.latest_np(n=n))
    else:
        p = client.latest_np(n=n)[0]
        print('Thread number: {0}\nActive? {1}\nRelative date: {2} hours ago'.format(p[0], p[1], p[2]))


def print_posts_timespan(start_date):
    print('\033[4m[<thread number>, <active?>, <relative date (H)>]\033[0m\n')
    print(client.posts_ts(start_date))


def print_country_s(start: str, end: str):
    print(client.c_stats(start, end))


def print_board_s(start: str, end: str):
    print('\033[4m[#new posts, #new threads, #posts per min, #words_written, date]\033[0m\n')
    print(client.b_stats(start, end))


def print_last_board_s(start: str, end: str):
    arr = client.b_stats(start, end)
    if arr is None:
        print('No analysis conduced on specified time span.')
    stats = arr[-1]
    print('# of new posts published: {0}\n# of new threads published {1}\nAverage posts/min: {2}\nTotal '
          'words written: {3}\nAnalysis conduced on: {4}'.format(stats[0], stats[1], stats[2], stats[3], stats[4]))


def print_get_t(tnum=0):
    t = client.thread(thread_number=tnum)
    if tnum == 0:
        print('\033[4m[<thread number>, <# images>, <# replies>, <date>, <subjectivity>, <polarity>]\033[0m\n')
        print(client.thread(thread_number=tnum))
    elif t is not None:
        thrd = t[0]
        im = t[1]
        rp = t[2]
        dt = t[3]
        ss = t[4]
        ps = t[5]
        print('Thread number: {0}\n# images: {1}\n# replies: {2}\nDate: {3}\nSubjectivity: {4}\nPolarity: {5}'.format(
            thrd, im, rp, dt, ss, ps))
    else:
        print(client.thread(thread_number=tnum))


def print_get_p(tnum, n=-1, msg=False):
    t = client.posts(thread_number=tnum, n=n, msg=msg)
    if n == 1:
        if msg:
            thrd = t[0]
            titl = t[1]
            tx = t[2]
            lnk = t[3]
            dt = t[4]
            ss = t[5]
            ps = t[6]
            print('Thread number: {0}\nTitle: {1}\nMessage: {2}\nLinks: {3}\nDate: {4}\nSubjectivity: {5}\nPolarity: '
                  '{6}'.format(thrd, titl, tx, lnk, dt, ss, ps))
        else:
            thrd = t[0]
            dt = t[1]
            ss = t[2]
            ps = t[3]
            print(
                'Thread number: {0}\nDate: {1}\nSubjectivity: {2}\nPolarity: {3}'.format(
                    thrd, dt, ss, ps))
    elif msg:
        print('\033[4m[<thread number>, <title>, <message>, <links>, <date>, <subjectivity>, <polarity>]\033[0m\n')
        print(client.posts(thread_number=tnum, n=n, msg=msg))
    elif not msg:
        print('\033[4m[<thread number>, <date>, <subjectivity>, <polarity>]\033[0m\n')
        print(client.posts(thread_number=tnum, n=n, msg=msg))


def print_add_t(title, username, text):
    t = client.add_t(title=title, username=username, text=text)
    thrd = t[0]
    titl = t[1]
    tx = t[2]
    usr = t[3]
    dt = t[4]
    print('Thread number: {0}\nTitle: {1}\nMessage: {2}\nUsername: {3}\nDate: {4}'.format(thrd, titl, tx, usr, dt))
    return thrd


def print_add_p(tnum, title, username, text):
    t = client.add_p(thread_number=tnum, title=title, username=username, text=text)
    thrd = t[0]
    titl = t[1]
    tx = t[2]
    usr = t[3]
    dt = t[4]
    print('Thread number: {0}\nTitle: {1}\nMessage: {2}\nUsername: {3}\nDate: {4}'.format(thrd, titl, tx, usr, dt))


def print_del_t(tnum):
    print(client.del_t(thread_number=tnum))


if __name__ == '__main__':
    client = Client()

    print_users()

    print_images()

    print_replies()

    print('\nBiggest file uploaded:')
    print_max_attach()

    print('\nAll attachments uploaded:')
    print_all_attach()

    print('\nFinding all thread in DB:')
    print_get_t()

    print('\nSearching for a thread:')
    print_get_t(tnum=233286661)

    print('\nSearching for a thread that does not exist:')
    print_get_t(tnum=564123)

    print('\nSearching for all posts of a thread:')
    print_get_p(tnum=233286661)

    print('\nSearching for 3 most recent posts, in a thread:')
    print_get_p(tnum=233286661, n=3)

    print('\nSearching for 3 most recent posts, including title and message in a thread:')
    print_get_p(tnum=233286661, n=3, msg=True)

    print('\nSearching most recent post, including the title and message, in a thread:')
    print_get_p(tnum=233286661, n=1, msg=True)

    print('\nSearching most recent post, excluding the title and message, in a thread:')
    print_get_p(tnum=233286661, n=1, msg=False)

    print('\nSearching posts of a thread that does not exist:')
    print_get_p(tnum=564123)

    print('\nCreating a new thread:')
    title = 'NO!'
    text = 'YOU...SHALL NOT...PASSSS!!!'
    username = 'Gandalf'
    thread_number = print_add_t(title=title, username=username, text=text)

    print('\nCreate a post on a thread:')
    title = 'GRRRAAWWWRRRRR'
    text = '*becomes basically lava*'
    username = 'The Barlog'
    print_add_p(tnum=thread_number, title=title, username=username, text=text)

    print('\nDeleting fetched thread:')
    print_del_t(tnum=233346446)

    print('\nDeleting created thread:')
    print_del_t(tnum=thread_number)

    print('\nSearching for latest posts:')
    print_latest_n_posts(n=1)

    print('\nSearching for latest 4 posts:')
    print_latest_n_posts(n=4)

    print('\nSearch for posts created after a date:')
    print_posts_timespan('24/1/2022')

    print('\nAnalysis on posts and threads:')
    print_board_s('1/1/2022', '25/1/2022')

    print('\nLast analysis conduced, in detail:')
    print_last_board_s('1/1/2022', '25/1/2022')

