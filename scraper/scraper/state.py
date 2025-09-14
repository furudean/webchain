from __future__ import annotations
import math, json, random, string, datetime
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


    # mode = 0 is my version of a hashing algorithm
    # def hash(self, key: str, mode=0):
    #     if mode:
    #         return hash(key) % self.tablesize
    #     else:
    #         key_num = 0
    #         for i in key:
    #             key_num += ord(i)

    #         key_num = math.fabs(key_num)
    #         A = (math.sqrt(5) - 1) / 2
    #         # print(A)
    #         # print(key_num*A)
    #         # print(math.modf(key_num*A))
    #         return math.floor(self.tablesize * math.modf(key_num*A)[0])


    # for hypothetical directly addressed table
    # def altInsert(self, node_to_insert: Node, index = -1):
    #     if index == -1:
    #         index = self.hash(node_to_insert.url)

    #     if self.node[index] != []:
    #     # try again : will scan up in sequence then down in sequence
    #         self.altInsert(node_to_insert, index+1)
    #         self.altInsert(node_to_insert, index-1)

    #     self.table[index].append(node_to_insert)
    #     return index

    # implements linear search instead of searching by computing hash


    # Returns Node object with url matching search_key if found, else returns -1
    # def findValueByURL(self, search_key):
    #     index = self.hash(search_key)
    #     if self.table[index] == []:
    #         print(f"Not found at {index}")
    #         return -1
    #     else:
    #         c = 0
    #         for i in self.table[index]:
    #             if i.url == search_key:
    #                 print(f"found it at {index} at position {c}")
    #                 return i
    #             c+=1
    #         print(f"Not found (collided) at {index}")
    #         return -1


    # def toDict(self):
    #     r = {}
    #     r.update({"tablesize" : self.tablesize})
    #     r.update({"start" : self.start})
    #     r.update({"end" : self.end})
    #     t = {}
    #     for i in range(0, self.tablesize):
    #         if not (self.table[i] == []):
    #             l = []
    #             for x in self.table[i]:
    #                 d = x.toDict()
    #                 l.append(d)
    #             t.update({i : l})
    #         else:
    #             t.update({i : self.table[i]})
    #     r.update({'table' : t})
    #     return r


    # def fromDict(self, d: dict):
    #     self.tablesize = -1
    #     self.table = []
    #     for (k,v) in d.items():
    #         if k == 'tablesize':
    #             self.tablesize = v
    #         elif k == 'start':
    #             self.start = v
    #         elif k == 'end':
    #             self.end = v
    #         elif k == 'table':
    #             l = len(v)
    #             for i in range(0,l):
    #                 x = v.pop(f'{i}')
    #                 if not (x == []):
    #                     o = []
    #                     for y in x:
    #                         n = Node('', None, None)
    #                         n.fromDict(y)
    #                         o.append(n)
    #                     self.table.append(o)
    #                 else:
    #                     self.table.append(x)


    # def serialize(self, filename:str | None = None):
    #     if filename:
    #         with open(f'../web/static/crawler/{filename}.json','w') as f:
    #             json.dump(self.toDict(),f)
    #     else:
    #         with open(f'../web/static/crawler/table.json','w') as f:
    #             json.dump(self.toDict(),f)

    # def deserialize(self,filename:str | None = None):
    #     if filename:
    #         with open(f'../web/static/crawler/{filename}.json','r') as f:
    #             self.fromDict(json.load(f))
    #     else:
    #         with open(f'../web/static/crawler/table.json','r') as f:
    #             self.fromDict(json.load(f))

# def random_url():
#     letters = string.ascii_lowercase
#     middle = ''.join(random.choice(letters) for i in range(20))
#     return ''.join(['https://',middle,'.com'])
