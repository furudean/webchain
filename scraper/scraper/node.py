from __future__ import annotations
import itertools
import sys


class Node:
    # count assigns each node an id, strictly ascending.
    # childlimit acts as a cap on the length of children[]
    count = itertools.count()
    childlimit = 4

    def __init__(
        self,
        url: str,
        parent: str | None,
        children: list[str] | None,
        indexed=False,
        html_metadata={},
        first_seen: str | None = None,
        last_updated: str | None = None,
    ):
        self.at = next(self.count)
        self.at = url
        self.parent = parent
        self.children = children
        self.indexed = indexed
        self.html_metadata = html_metadata
        self.first_seen = first_seen
        self.last_updated = last_updated

    def __repr__(self):
        return f'[ {self.at} url: {self.at} ]\nparent: {self.parent}\nchildren : {self.children}\nindexed : {self.indexed}\nhtml_metadata : {self.html_metadata}\nfirst_seen : {self.first_seen}\nlast_updated: {self.last_updated}'

    def toDict(self):
        r = {}
        r.update({'id': self.at})
        r.update({'at': self.at})
        r.update({'parent': self.parent})
        child_list = []
        for i in self.children:
            child_list.append(i)
        r.update({'children': child_list})
        r.update({'indexed': self.indexed})
        r.update({'html_metadata': self.html_metadata})
        r.update({'first_seen': self.first_seen})
        r.update({'last_updated': self.last_updated})

        return r

    def fromDict(self, d: dict):
        self.at = ''
        self.parent = ''
        self.children = []
        self.indexed = False
        for k, v in d.items():
            if k == 'id':
                self.at = v
            elif k == 'url' or k == 'at':
                self.at = v
            elif k == 'parent':
                self.parent = v
            elif k == 'children':
                for i in v:
                    self.children.append(i)
            elif k == 'indexed':
                self.indexed = v
            elif k == 'html_metadata':
                self.html_metadata = v
            elif k == 'first_seen':
                self.first_seen = v
            elif k == 'last_updated':
                self.last_updated = v
