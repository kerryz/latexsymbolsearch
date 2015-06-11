# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division

import os

from whoosh.index import create_in, open_dir
from whoosh.fields import (
    Schema,
    TEXT, ID, NGRAM, STORED
)
from whoosh import qparser
from whoosh.query import FuzzyTerm
from whoosh.analysis import StandardAnalyzer

from preprocesser import get_documents

from global_constants import COMMANDS, CONTENT, HTML

INDEX_DIR = os.path.join("..", "index")
CREATE_NEW_INDEX = True  # create a new index from scratch


def main():
    schema = get_schema()

    # create index directory if not exists
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)
        ix = create_in(INDEX_DIR, schema)

    if CREATE_NEW_INDEX:
        ix = create_in(INDEX_DIR, schema)
        writer = ix.writer()
        # add documents to index
        documents = get_documents()
        for doc in documents:
            writer.add_document(**doc.get_kwargs())
        writer.commit()
    else:
        ix = open_dir(INDEX_DIR)

    """
    # search the index
    with ix.searcher() as searcher:
        # parser = get_fuzzy_qparser([COMMANDS, CONTENT], schema)
        my_query = "sum"

        cmd_parser = get_fuzzy_qparser([COMMANDS], schema)
        cmd_query = cmd_parser.parse(my_query)
        cmd_results = searcher.search(cmd_query, limit=5)

        content_parser = get_fuzzy_qparser([CONTENT], schema)
        content_query = content_parser.parse(my_query)
        content_results = searcher.search(content_query, limit=10)

        cmd_results.upgrade_and_extend(content_results)
        print len(cmd_results)
        for r in cmd_results:
            print type(r)
            print r[COMMANDS]
    """


class MyFuzzyTerm(FuzzyTerm):
    """http://stackoverflow.com/a/30502661/3694224"""
    def __init__(self, fieldname, text, boost=1.0, maxdist=3, prefixlength=1, constantscore=True):
        super(MyFuzzyTerm, self).__init__(
            fieldname, text, boost, maxdist, prefixlength, constantscore)


def get_schema():
    return Schema(
        img_srcs=ID(stored=True),  # use IDLIST instead?
        # commands=NGRAM(stored=True, minsize=2, maxsize=10, field_boost=20.0),
        commands=TEXT(stored=True, field_boost=20.0, analyzer=StandardAnalyzer(stoplist=None)),
        keywords=TEXT(stored=True, field_boost=15.0, analyzer=StandardAnalyzer(stoplist=None)),
        content=TEXT(stored=False),
        html=STORED,
        # content=NGRAM(stored=True, minsize=3, maxsize=10),
    )


def get_exact_qparser(fields, schema):
    """
    Parameters
    ----------
    fields : list
        [field1, field2, ...]
    """
    parser = qparser.MultifieldParser(fields, schema=schema)
    return parser


def get_exact_or_qparser(fields, schema):
    """
    Parameters
    ----------
    fields : list
        [field1, field2, ...]
    """
    og = qparser.OrGroup.factory(0.9)  # makes documents that contain more keywords score higher
    parser = qparser.MultifieldParser(fields, schema=schema, group=og)
    return parser


def get_fuzzy_qparser(fields, schema):
    """
    Parameters
    ----------
    fields : list
        [field1, field2, ...]
    """
    og = qparser.OrGroup.factory(0.9)  # makes documents that contain more keywords score higher
    parser = qparser.MultifieldParser(fields, schema=schema, group=og, termclass=MyFuzzyTerm)
    parser.add_plugin(qparser.FuzzyTermPlugin())  # only for query terms ending with ~
    return parser


if __name__ == "__main__":
    main()
