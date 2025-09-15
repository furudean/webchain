from __future__ import annotations
import datetime
from scraper.node import Node

class StateTable:

    tablesize = 0
    start:datetime = datetime.datetime.min
    end:datetime = datetime.datetime.min

    def __init__(self, start: datetime.datetime | None = None, end: datetime.datetime | None = None):
        self.nodes = []
        self.start = start
        self.end = end


    def __repr__(self, mode: 0):
        r = ''
        for i in range(0, len(self.nodes)):
            s = f'{i} : {self.nodes[i]}\n'
            r += s
        d = f"{datetime.timedelta.total_seconds(datetime.datetime.fromisoformat(self.end) - datetime.datetime.fromisoformat(self.start))}"
        print(f"start : [ {self.start} ]\nend : [ {self.end} ]\nruntime : {d} seconds \n{r}")


    def view(self):
        r = ''
        for i in range(0, len(self.nodes)):
            s = f'{i} : {self.nodes[i]}\n'
            r += s
        d = f"{datetime.timedelta.total_seconds(datetime.datetime.fromisoformat(self.end) - datetime.datetime.fromisoformat(self.start))}"
        print(f"start : [ {self.start} ]\nend : [ {self.end} ]\nruntime : {d} seconds \n{r}")


    def setStart(self, start : datetime):
        self.start = start


    def setEnd(self, end : datetime):
        self.end = end


    def insert(self, node_to_insert: Node):
        self.nodes.append(node_to_insert)
        return len(self.nodes)-1


    def find(self, search_key):
        for i in range(0, len(self.nodes)):
                if self.nodes[i].url == search_key:
                    return i
        return -1


    def log(self):
        nodes = []
        for i in range(0, len(self.nodes)):
            nodes.append(self.nodes[i].toDict())
        r = {}
        r.update({'nodes' : nodes})
        r.update({"start" : self.start})
        r.update({"end" : self.end})
        return r


    def fromData(self, d: dict):
        nodelist = []
        for (k,v) in d.items():
            if k == "nodes":
                nodelist = v
            elif k == 'start':
                self.start = v
            elif k == 'end':
                self.end = v
        for i in nodelist:
            n = Node('',None,None)
            n.fromDict(i)
            self.insert(n)
        return self


# def random_url():
#     letters = string.ascii_lowercase
#     middle = ''.join(random.choice(letters) for i in range(20))
#     return ''.join(['https://',middle,'.com'])
