# from __future__ import annotations

import en_core_web_lg
from rake_spacy import Rake
from spacy.language import Language
from spacy.tokens import Doc
import math
from spacytextblob.spacytextblob import SpacyTextBlob



@Language.factory('xtract_kw', default_config={'num_kw': 3})
def create_kw_xtractor(nlp: Language, name: str, num_kw: int):
    return KwXtraktor(nlp, num_kw)


class KwXtraktor:
    def __init__(self, nlp: Language, num_kw: int):
        self.__rake = Rake(nlp=nlp)
        self.__num_kw = num_kw + 1

    def __call__(self, doc: Doc) -> Doc:
        result = self.__rake.extract_keywords_from_doc(doc)
        dd = [(i.text_with_ws, i.rank) for f, d in result for i in d]
        doc.user_data = {'kw': {k: math.log(v) for k, v in sorted(dd, key=lambda x: x[1])[:-self.__num_kw:-1]},
                         'sentiment': {'polarity': doc._.polarity if doc._.polarity is not None else 0.0,
                                       'subjectivity': doc._.subjectivity if doc._.subjectivity is not None else 0.0}}
        return doc


class Analyzer:
    def __init__(self, n_kws: int):
        self.__nlp = en_core_web_lg.load()
        self.__nlp.add_pipe('spacytextblob')
        self.__nlp.add_pipe('xtract_kw', config={'num_kw': n_kws}, last=True)
        #self.__nlp.disable_pipes(*["tok2vec", "tagger", "parser", "attribute_ruler", "lemmatizer"])

    def anyalze(self, doc: list, n_proc: int, keywords=True): # -> [Doc | tuple[Doc, ...] | list[tuple[float, float]]]:
        if not keywords:
            self.__nlp.disable_pipes('xtract_kw')
            docs = [(d._.polarity if d._.polarity is not None else 0.0,
                     d._.subjectivity if d._.subjectivity is not None else 0.0)
                    for d in self.__nlp.pipe(doc, n_process=n_proc)]
        else:
            docs = self.__nlp.pipe(doc, n_process=n_proc)
        if not keywords:
            self.__nlp.enable_pipe('xtract_kw')
        return docs
