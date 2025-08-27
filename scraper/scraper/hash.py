import math, random, string

class Link:
    def __init__(self, value, next=None):
        self.value = value
        self.next = next

    def __repr__(self):
        return f"val: ({self.value}) next: ({self.next})"

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

    def insert(self, url):
        index = self.hash(url)
        if self.table[index] is None:
            self.table[index] = Link(url)
            return 0
        else:
            current = self.table[index]
            while current.next is not None:
                current = current.next
            current.next = Link(url)
            print(f"collided link: [{self.table[index]}] ")
            print(f"to link: [{current.next}]")

            # self.table[index].next = Link(url)
            return index

    def evaluate(self):
        rval = 0
        for i in range(0,self.tablesize):
            if self.table[i] is not None:
                rval +=1
        return rval

def randomstring():
    letters = string.ascii_lowercase
    middle = ''.join(random.choice(letters) for i in range(20))
    return ''.join(['https://',middle,'.com'])

# T = HashTable()
# print(T.hash(randomstring()))

# collision_list = []

# for i in range(0,100):
#     collision_list.append(T.insert(randomstring()))

# collision_list = list(filter((0).__ne__, collision_list))
# print(collision_list)

# for i in collision_list:
#     print(T.table[i])
# print(T.evaluate())

# print(T.hash("https://chain-staging.milkmedicine.net"))

