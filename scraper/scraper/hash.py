from __future__ import annotations
import math, json, random, string
from scraper.node import Node

class HashTable:

    tablesize = 16


    def __init__(self, tablesize=None):
        if tablesize:
            self.tablesize = tablesize
        l = []
        for i in range(0, self.tablesize):
            l.append([])
        self.table = l


    def __repr__(self):
        return f"{self.table}"


    def hash(self, key: str, mode=1):
        if mode:
            return hash(key) % self.tablesize
        else:
            key_num = 0
            for i in key:
                key_num += ord(i)

            key_num = math.fabs(key_num)
            A = (math.sqrt(5) - 1) / 2
            # print(A)
            # print(key_num*A)
            # print(math.modf(key_num*A))
            return math.floor(self.tablesize * math.modf(key_num*A)[0])


    def insert(self, node_to_insert: Node):
        index = self.hash(node_to_insert.url)
        self.table[index].append(node_to_insert)
        return index


    # Returns Node object with url matching search_key if found, else returns -1
    def findValue(self, search_key):
        index = self.hash(search_key)
        if self.table[index] == []:
            print("Not found")
            return -1
        else:
            c = 0
            for i in self.table[index]:
                if i.url == search_key:
                    print(f"found it at {index} at position {c}")
                    return i
                c+=1
            print("Not found (collided)")
            return -1


    def evaluate(self):
        rval = 0
        for i in range(0,self.tablesize):
            if self.table[i] is not None:
                rval +=1
        return rval


    def toDict(self):
        r = {}
        r.update({"tablesize" : self.tablesize})
        t = {}
        for i in range(0, self.tablesize):
            if not (self.table[i] == []):
                l = []
                for x in self.table[i]:
                    d = x.toDict()
                    l.append(d)
                t.update({i : l})
            else:
                t.update({i : self.table[i]})
                # print("--------------------------")
        r.update({'table' : t})
        return r


    def fromDict(self, d: dict):
        self.tablesize = -1
        self.table = []
        for (k,v) in d.items():
            if k == 'tablesize':
                self.tablesize = v
            elif k == 'table':
                # print(v)
                l = len(v)
                for i in range(0,l):
                    x = v.pop(f'{i}')
                    # print(x)
                    if not (x == []):
                        o = []
                        for y in x:
                            n = Node('', None, None)
                            n.fromDict(y)
                            o.append(n)
                        self.table.append(o)
                    else:
                        self.table.append(x)

    def serialize(self):
        with open(f'table.json','w') as f:
            json.dump(self.toDict(),f)

    def deserialize(self):
        with open(f'table.json','r') as f:
            self.fromDict(json.load(f))

# def random_url():
#     letters = string.ascii_lowercase
#     middle = ''.join(random.choice(letters) for i in range(20))
#     return ''.join(['https://',middle,'.com'])
