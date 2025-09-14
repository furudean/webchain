from __future__ import annotations
import itertools
import sys


class Node:
    # count assigns each node an id, strictly ascending.
    # childlimit acts as a cap on the length of children[]
    count = itertools.count()
    childlimit = 4


    def __init__(self, url: str, parent: str | None, children: list[str] | None, indexed = False, html_metadata = {}):
        self.id = next(self.count)
        self.url = url
        self.parent = parent
        self.children = children
        self.indexed = indexed
        self.html_metadata = html_metadata


    def __repr__(self):
        return f'[ {self.id} url: {self.url} ]\nparent: {self.parent}\nchildren : {self.children}\nindexed : {self.indexed}\nhtml_metadata : {self.html_metadata}\n'


    def toDict(self):
        r = {}
        r.update({'id' : self.id})
        r.update({'at' : self.url})
        r.update({'parent' : self.parent})
        child_list = []
        for i in self.children:
            child_list.append(i)
        r.update({'children' : child_list})
        r.update({'indexed': self.indexed})
        r.update({'html_metadata': self.html_metadata})
        return r


    def fromDict(self, d: dict):
        self.id = -1
        self.url = ''
        self.parent = ''
        self.children = []
        self.indexed = False
        for (k,v) in d.items():
            if k == 'id':
                self.id = v
            elif k == 'url' or k == 'at':
                self.url = v
            elif k == 'parent':
                self.parent = v
            elif k == 'children':
                for i in v:
                    self.children.append(i)
            elif k == 'indexed':
                self.indexed = v
            elif k == 'html_metadata':
                self.html_metadata = v


    # if free slot exists, creates a leaf node from child_url and adds as a child.
    # this might never get used. for one, since an added child with children itself would have to have the children linked in a separate function call.
    # For now i'll leave this here since replaceChild depends on it
    def addChild(self, child_url: str | None):
        if len(self.children) < self.childlimit:
            self.children.append(child_url)
        return

    # to_remove is index of child to be removed, passing nothing removes latest node
    def removeChild(self, to_remove=None):
        if to_remove is None:
            self.children.pop(len(self.children)-1)
        elif to_remove in range(0, len(self.children)):
            self.children.pop(to_remove)
        else:
            print('error: index out of bounds (self.children)')
            sys.exit(1)

    # to_replace is index of child to be replaced, passing nothing replaces latest node
    def replaceChild(self, child_url: str | None, to_replace=None):
        self.removeChild(to_replace)
        self.addChild(child_url)


