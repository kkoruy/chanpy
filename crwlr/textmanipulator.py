import html
import re

from nltk.corpus import stopwords
from textblob import TextBlob


class TextManipulator:
    def __init__(self):
        self.__ws = re.compile(r'([ ])+', flags=re.MULTILINE)
        self.__utm = re.compile(r'([\S]+)(\?utm_[\S]+)', flags=re.MULTILINE)
        self.__bq = re.compile(r'<blockquote[a-zA-Z0-9 \"=>]{37}', flags=re.MULTILINE)
        self.__yt = re.compile(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)(\S)*', flags=re.MULTILINE)
        self.__lnk = re.compile(r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])',
                                flags=re.MULTILINE)
        self.__rp = re.compile(
            r'<a href=\"/((pol/thread/[0-9]{3,9}#p[0-9]{3,9})|(/boards\.4chan(nel)?\.org/[a-z0-9/]{1,19}/?)((thread/)|(catalog#s=)[a-zA-Z0-9%/\-.,:$&]{,33})?([0-9]{3,9}#p[0-9]{3,9})?)\" class=\"quotelink\">(&gt;){2,4}(([0-9]{3,9})|(/[a-z0-9/]{1,9}/([a-z0-9/]{2,9})?))</a>',
            flags=re.MULTILINE)
        self.__pg = (re.compile(r'\bi\'*m\b', flags=re.MULTILINE),
                     re.compile(r'\b(he|she|it|we|they|you|i)\'?ll\b', flags=re.MULTILINE),
                     re.compile(r'\b(he|she|it|we|they|you|i)\'?d\b', flags=re.MULTILINE),
                     re.compile(r'\b(we|they|you)\'?re\b', flags=re.MULTILINE),
                     re.compile(r'\b(we|they|you|i)\'?ve\b', flags=re.MULTILINE),
                     re.compile(r'\b(he|she|it)\'?s\b', flags=re.MULTILINE),
                     re.compile(
                         r'\b(lel|kek|lol|like|fuck|shit|kys|tbh|[a-z]{2}|wtf|lmao|lmfao|pls|link|eh|muh|omf?g|btfo|lulz|btw|anon[s]?)\b',
                         flags=re.MULTILINE),
                     re.compile(r'(n[e*][g*][r*][o*][e*]?|(n[i*][g*]{2}([e*][r*]|[a*])))[sz*]?', flags=re.MULTILINE),
                     re.compile(r'\b((jews?)|(k[i*]kes?))\b', flags=re.MULTILINE),
                     re.compile(r'\b(v[a*]([x*]{1,2}|[c*]{1,2}(ines?)))\b', flags=re.MULTILINE))
        self.__w = re.compile(r'\w+', flags=re.MULTILINE)
        self.__twitter = re.compile(r'^(https?://)?(mobile\.)?(twitter\.com/[a-zA-Z0-9_]*/status/[0-9]*)')
        self.__lnk2 = re.compile(r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])',
                                 flags=re.MULTILINE)
        self.__meta_description = re.compile(r'^([0-9.]+[kK]? Likes, [0-9.]+[kK]? Comments - )(.*)(on Instagram: )(.*)',
                                             flags=re.MULTILINE)
        self.__stopwordsset = set(stopwords.words('english') + ['actually', 'basically', 'literally', 'really', 'new',
                                                                'yeah', 'talk'])
        self.__tag_dict = {"J": 'a', "N": 'n', "V": 'v', "R": 'r'}

    @property
    def rgx_twttr(self):
        return self.__twitter

    @property
    def rgx_lnk2(self):
        return self.__lnk2

    @property
    def rgx_meta(self):
        return self.__meta_description

    def clean_text(self, text: str, rm_tags=False, rm_replytos=False, rm_links=False, rm_utm=False, escape=True,
                   length=-1) -> str:
        if rm_tags:
            text = self.remove_tags(text)
        if rm_replytos:
            text = self.extract_replied_posts(text)[1]
        if rm_utm:
            text = self.remove_utm(text)
        if rm_links:
            text = self.replace_links(text)
        if (length > -1) and (len(text) > length):
            i = text.rfind(' ', 0, length)
            if i == -1:
                text = text
            else:
                text = text[:i]
        if escape:
            text = self.safe_escape(text)
        return text

    def safe_escape(self, text: str) -> str:
        for char in '{}[]:;*|':
            text = text.replace(char, '')
        text = html.escape(text, quote=True).encode('ascii', 'xmlcharrefreplace')
        text = text.strip()
        return text.decode('utf-8')

    def remove_tags(self, text: str) -> str:
        for r in (('<wbr>', ''), ('<em>', ''), ('</em>', ''), ('</span>', ''),
                  ('<span class="quote">', ''), ('<br>', '\n'), ('<p>', '\n'), ('</p>', '\n'), ('</blockquote>', '')):
            text = text.replace(*r)
        return re.sub(self.__bq, '', text)

    # def remove_replytos(self, text):
    #    s = re.sub(r'&gt;&gt;[0-9]{9}', '', text, flags=re.MULTILINE)

    def remove_utm(self, text: str) -> str:
        try:
            i = text.find('?utm')
            if i == -1:
                if text == '':
                    return ''
                return text[:i]  # + text[i] # the text[i] returns the last char of the string
            return self.remove_utm(text[min(text[i + 4:].find(char) for char in ' \n'):])
        except IndexError as ie:
            print(ie, '\n\n')
            print(text.find('?utm'), str)
        return input()

    def truncate_ws(self, text: str) -> str:
        try:
            if text == '':
                return ''
            i = text.find('  ')
            if i == -1:
                return text if text[-1] != ' ' else text[:-1]
            j, k = i + 2, len(text)
            while j < k and text[j] == ' ':
                j += 1
            if k > 256:
                split = (k - j) // 2
                return text[:i] + ' ' + self.truncate_ws(text[j:split]) + self.truncate_ws(text[split:])
            return text[:i] + ' ' + self.truncate_ws(text[j:])
        except (RecursionError, IndexError, TypeError, ValueError) as e:
            print('TRUNCATE WHITESPACE:\n', e)
            print(text)
            input('Return: ')
            return ''

    def replace_links(self, text: str) -> str:
        text = re.sub(self.__yt, '[youtube]', text)
        return re.sub(self.__lnk, '[link]', text)

    def extract_replied_posts(self, text: str) -> tuple[list[int, ...], str]:
        text = re.sub(self.__rp, '', text)
        link_token1, link_token2 = '<a href="#p', '</a>'
        token = 'class=\"quotelink\">&gt;&gt;'
        repliedposts = []
        message = ''
        if token in text:
            try:
                if link_token1 in text:
                    s1 = text.index(token) + len(token)
                    message += text[:text.index(link_token1)]
                    repliedposts.append(int(text[s1:(s1 + 9)]))
                rp2, msg2 = self.extract_replied_posts(text[text.index(link_token2) + len(link_token2):])
                for reply in rp2:
                    if reply not in repliedposts:
                        repliedposts.append(int(reply))
                message += msg2
            except (ValueError, IndexError) as e:
                print(e)
                print(text)
        else:
            message = text
        return repliedposts, message

    def prep_grammar(self, text: str) -> str:
        text = html.unescape(text)
        text = text.lower()
        for r in (('\n', ' '), ('%', ' percent'), ('[youtube]', ''), ('[link]', '')):
            text = text.replace(*r)
        text = self.truncate_ws(text)
        for rgx in self.__pg[:7]:
            text = re.sub(rgx, '', text)
        for rgx, sub in zip(self.__pg[7:], ('nwords', 'jews', 'vaccine')):
            text = re.sub(rgx, sub, text)
        for c in '#><|\":;(){}[]^*_=+@':#'.#,-!?><|\":;(){}[]^&*_=+@':
            text = text.replace(c, '')
        text = ' '.join(set(text.split(' ')).difference(self.__stopwordsset))
        text = text.replace('\'', '')
        for r in (('yall', 'you all'), ('gotta', 'got to'), ('thats', 'that is')):
            text = text.replace(*r)
        text = re.sub(self.__ws, ' ', text)
        text = self.lemmatize_with_postag(text.strip())
        text = list(set(text).difference(set(['make', 'use', 'fuck', 'want', 'look', 'come', 'think', 'time',
                                              'good', 'guy', 'year', 'say', 'try', 'na', 'know', 'thing'] + [word.replace('\'', '')
                                                                        for word in stopwords.words('english')])))
        text = ' '.join(text)
        return text

    def lemmatize_with_postag(self, sentence: str) -> list[str, ...]:
        sent = TextBlob(sentence)
        words_and_tags = [(w, self.__tag_dict.get(pos[0], 'n')) for w, pos in sent.tags]
        lemmatized_list = [wd.lemmatize(tag) for wd, tag in words_and_tags]
        return self.unify_words(lemmatized_list)

    def unify_words(self, wordlist):
        rmwords = []
        wordlist = sorted(wordlist, key=lambda n: len(n))
        for i in range(len(wordlist) - 1):
            if i in rmwords:
                continue
            word = wordlist[i]
            lw1, lw3 = len(word) + 1, len(word) + 3
            for j in range(i + 1, len(wordlist)):
                if j in rmwords:
                    continue
                nxtword = wordlist[j]
                if len(nxtword) < lw1:
                    continue
                if len(nxtword) > lw3:
                    break
                if nxtword.startswith('fuck') or (
                        (nxtword[-3:] == 'ing' or nxtword[-2:] in ['in', 'ed'] or nxtword[-1] == 's') and (
                        nxtword.startswith(word[:-1]) or nxtword.startswith(word[:-2]))):
                    rmwords.append(j)
        if len(rmwords) > 0:
            for idx in sorted(rmwords, reverse=True):
                wordlist.pop(idx)
        return wordlist

    def word_count(self, txt: str) -> int:
        for r in (('[youtube]', ''), ('[link]', ''), ('\n', ' ')):
            txt = txt.replace(*r)
        words = re.findall(self.__w, txt)
        return len(words)
