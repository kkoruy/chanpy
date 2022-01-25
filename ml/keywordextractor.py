import warnings
from multiprocessing import Queue
import numpy as np
import spacy

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import NMF, LatentDirichletAllocation

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

"""
=======================================================================================
Topic extraction with Non-negative Matrix Factorization and Latent Dirichlet Allocation
=======================================================================================

This is an example of applying :class:`sklearn.decomposition.NMF` and
:class:`sklearn.decomposition.LatentDirichletAllocation` on a corpus
of documents and extract additive models of the topic structure of the
corpus.  The output is a list of topics, each represented as a list of
terms (weights are not shown).

Non-negative Matrix Factorization is applied with two different objective
functions: the Frobenius norm, and the generalized Kullback-Leibler divergence.
The latter is equivalent to Probabilistic Latent Semantic Indexing.

The default parameters (n_samples / n_features / n_components) should make
the example runnable in a couple of tens of seconds. You can try to
increase the dimensions of the problem, but be aware that the time
complexity is polynomial in NMF. In LDA, the time complexity is
proportional to (n_samples * iterations).

"""
# n_samples = 2000
# n_features = 1000
# n_components = 10
# n_top_words = 20


def __extract(maxdf, mindf, num_features, lang, num_components, num_of_keywords, data_samples):
    print("LSA", num_components, len(data_samples), end=' ')
    max_doc_freq = maxdf
    min_doc_freq = mindf
    n_features = num_features
    language = lang
    n_components = num_components
    n_top_words = num_of_keywords
    kw = []
    tfidf_vctzr = TfidfVectorizer(max_df=max_doc_freq, min_df=min_doc_freq,
                                  max_features=n_features, stop_words=language)
    tf_vctzr = CountVectorizer(max_df=max_doc_freq, min_df=min_doc_freq,
                               max_features=n_features, stop_words=language)
    nmf1 = NMF(n_components=n_components, random_state=1, alpha_W=.1, alpha_H=.1, l1_ratio=.5)
    nmf2 = NMF(n_components=n_components, random_state=1, beta_loss='kullback-leibler',
               solver='mu', max_iter=1024, alpha_W=.1, alpha_H=.1, l1_ratio=.5)
    lda = LatentDirichletAllocation(n_components=n_components, max_iter=14,
                                    learning_method='online', learning_offset=50., random_state=0)
    tfidf = tfidf_vctzr.fit_transform(data_samples)
    tf = tf_vctzr.fit_transform(data_samples)
    tfidf_feature_names = tfidf_vctzr.get_feature_names_out()
    # print(tfidf_feature_names)
    numfn = len(tfidf_feature_names)
    wd = {}
    for topic_idx, topic in enumerate(nmf1.fit_transform(tfidf).transpose()):
        indices = topic.argsort()[:-n_top_words - 1:-1]
        kws = [tfidf_feature_names[i] for i in indices if i < numfn]
        for k, v in zip(kws, topic[:-n_top_words - 1:-1]):
            # wd[k] = v if k not in wd.keys() or v < wd[k] else wd[k]
            # wd[k] = v if k not in wd.keys() else wd[k] + v
            wd[k] = [v] if k not in wd.keys() else wd[k] + [v]
        kw.append([tfidf_feature_names[i]
                   for i in indices if i < numfn])
    for topic_idx, topic in enumerate(nmf2.fit_transform(tfidf).transpose()):
        indices = topic.argsort()[:-n_top_words - 1:-1]
        kws = [tfidf_feature_names[i] for i in indices if i < numfn]
        for k, v in zip(kws, topic[:-n_top_words - 1:-1]):
            # wd[k] = v if k not in wd.keys() or v < wd[k] else wd[k]#wd[k] + v if k in wd.keys() else wd[k] = v
            # wd[k] = v if k not in wd.keys() else wd[k] + v
            wd[k] = [v] if k not in wd.keys() else wd[k] + [v]
        kw.append(kws)

    tf_feature_names = tf_vctzr.get_feature_names_out()
    numfn = len(tf_feature_names)
    for topic_idx, topic in enumerate(lda.fit_transform(tf).transpose()):
        indices = topic.argsort()[:-n_top_words - 1:-1]
        kws = [tf_feature_names[i] for i in indices if i < numfn]
        for k, v in zip(kws, topic[:-n_top_words - 1:-1]):
            # wd[k] = v if k not in wd.keys() or v < wd[k] else wd[k]
            # wd[k] = v if k not in wd.keys() else wd[k] + v
            wd[k] = [v] if k not in wd.keys() else wd[k] + [v]
        kw.append([tf_feature_names[i] for i in indices if i < numfn])
    s0 = set()
    for i, s1 in enumerate(kw[:-1]):
        for s2 in kw[i + 1:]:
            s0 = s0 | (set(s1) & set(s2))
    wl = list(s0)
    for k, v in wd.items():
        wd[k] = sum(v) / float(len(v))
    weights = np.argsort([wd[w] for w in wl])[::-1]
    return [wl[j] for j in weights[-14:]]


def keyword_extraction_worker(q: Queue) -> Queue:
    pid, msgs = q.get()
    lengths = [len(v) for v in msgs.values()]
    if len(lengths) > 0:
        comps = max(lengths)
    else:
        comps = 14
        print(msgs)
    keywords = {tnum: [] for tnum in msgs.keys()}
    for i, (k, v) in enumerate(msgs.items()):
        keywords[k] = __extract(1.0, 5, 8192, 'english', 14, 14, v)
        # print('\n' + '\n'.join(msgs[:2]))
        print(f"[{pid}]({i}) {k}:\t{keywords[k]}")
    print('\n')
    return q.put(keywords)


def keyword_extraction(msgs: dict) -> dict:
    keywords = {tnum: [] for tnum in msgs.keys()}
    for k, v in msgs.items():
        keywords[k] = list(set(__extract(1.0, 2, 8192, 'english', 14, 14, v)))
        print(f"{k}:\t{keywords[k]}")
    return keywords
