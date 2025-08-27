from __future__ import annotations
import math, random, string
from scraper.node import Node

class Link:
    def __init__(self, value: Node | None, next=None):
        self.value = value
        self.next = next

    def __repr__(self):
        return f"val: ({self.value}) next: ({self.next})"

    def setValue(self, value: Node):
        self.value = value

    def getValue(self):
        return self.value

    def setNext(self, next: Link):
        self.next = next

    def getNext(self):
        return self.next


class HashTable:

    tablesize = 256

    def __init__(self, tablesize=None):
        if tablesize:
            self.tablesize = tablesize

        self.table = [None]*self.tablesize

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
        if self.table[index] is None:
            self.table[index] = Link(node_to_insert)
            return index
        else:
            current = self.table[index]
            while current.next is not None:
                current = current.next
            current.setNext(Link(node_to_insert))
            # print(f"collided link: [{self.table[index]}] ")
            # print(f"to link: [{current.next}]")
            return index


    # Returns Node object with url matching search_key if found, else returns -1
    def findValue(self, search_key):
        index = self.hash(search_key)
        if self.table[index] is None:
            print("Not found")
            return -1
        else:
            if self.table[index].value.url == search_key:
                print(f"found: {search_key} at {index} ")
                return self.table[index].value
            else:
                current = self.table[index]
                while current is not None and not (current.value.url == search_key):
                    current = current.next
                    if current.value.url == search_key:
                        print(f"found: {search_key} at {index} (collided)")
                        print(f"linked list at {index}: {self.table[index]}")
                        return current.value
                print("Not found in linked list")
                return -1

    def evaluate(self):
        rval = 0
        for i in range(0,self.tablesize):
            if self.table[i] is not None:
                rval +=1
        return rval

def random_url():
    letters = string.ascii_lowercase
    middle = ''.join(random.choice(letters) for i in range(20))
    return ''.join(['https://',middle,'.com'])

# T = HashTable()

# url_list = []
# for i in range(0,100):
#     url_list.append(random_url())

# collision_list = []

# for i in range(0,100):
#     collision_list.append(T.insert(url_list[i]))

# collision_list = list(filter((0).__ne__, collision_list))

# for i in url_list:
#     T.findValue(i)

# for i in collision_list:
#     collided_urls.append(url_list[i])
# print(collision_list)

# for i in collision_list:
#     print(T.table[i])
# print(T.evaluate())

# print(T.hash("https://chain-staging.milkmedicine.net"))

