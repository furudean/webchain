import itertools


'''
Still need to do:
1.  create whatever "shell" these nodes will live in.
    ideally this shell will have methods like (or the ability to do) things like
    - find_by_id
    - find_by_url
    - be the "memory" from which nodes are added or deleted (i.e. serve as a master record of all active nodes) [see todos in remove function]

2.  make it so i can decrement count according to deletion from memory: see test ex below
'''

class Node:

    count = itertools.count()

    def __init__(self, url, parent=None, left=None, right=None):
        self.id = next(self.count)
        self.url = url
        self.parent = parent
        self.left = left
        self.right = right

    def __repr__(self):
        if self.left and self.right:
            return f"{self.id} {self.url} {self.parent} {self.left.url} {self.right.url}"
        elif self.left:
            return f"{self.id} {self.url} {self.parent} {self.left.url} {self.right}"
        elif self.right:
            return f"{self.id} {self.url} {self.parent} {self.left} {self.right.url}"
        else:
            return f"{self.id} {self.url} {self.parent} {self.left} {self.right}"




    @classmethod
    def root(cls, url, left_url=None, right_url=None):
        root = Node(url)
        root.addChild(left_url)
        root.addChild(right_url)
        return root

    @classmethod
    def leaf(cls, url, parent):
        return Node(url, parent, None, None)

    # if free slot exists, creates a leaf node from child_url and adds as a child.
    def addChild(self, child_url):
        if self.left is None:
            self.left=Node.leaf(child_url,self.url)
            return
        if self.left is not None:
            if self.right is None:
                self.right = Node.leaf(child_url,self.url)
                return
            else:
                return

    # passing 0 deletes left child, passing 1 removes right child, passing neither treats it as a stack
    def removeChild(self, to_remove=-1):
        if not to_remove:
            # to do : Delete left Node in memory
            self.left = None
            return
        elif to_remove == 1:
            # to do : Delete right node in memory
            self.right = None
            return
        else:
            # default behavior : "pops" the most recent child. if both slots filled, pops right. else pops left.
            if self.right is None:
                if self.left is None:
                    return
                else:
                    # to do : Delete left Node in memory
                    self.left = None
                    return
            else:
                # to do : Delete right node in memory
                self.right = None
                return

    # pass 1 to replace right slot, pass 0 to replace left slot.
    def replaceChild(self, child_url, to_replace):
        self.removeChild(to_replace)
        self.addChild(child_url)

    # prints subtree
    def printSubtree(self):
        printTree(self)

#relies on the root itself being static, prints entire tree
def printTree(root: Node):
    print(root)
    if root.left:
        printTree(root.left)
    if root.right:
        printTree(root.right)


#######################################################

#######################################################

# Dummy sites
a_url = "chain.milkmedicine.net"
b_url = "nekopath.fun"
c_url = "himawari.fun"
d_url = "pixiv.net"



root = Node.root(a_url, b_url, c_url)
# printTree(root)

neko = root.left
neko.addChild(d_url)
# printTree(root)
neko.printSubtree()
# root.printChain()

# root.replaceChild(d_url, 0)
# root.printChain()

# root.replaceChild(b_url, 0)
# root.printChain()

# root.addChild(d_url)
# root.printChain()

# root.removeChild()
# root.printChain()

# root.addChild(d_url)
# root.printChain()

# root.removeChild()
# root.removeChild()
# root.printChain()

