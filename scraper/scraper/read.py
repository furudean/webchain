from scraper.crawl import crawl, CrawledNode
from scraper.node import Node
from scraper.hash import HashTable
from datetime import datetime, timezone
import json as jjson
import time

async def read_chain_into_table(root: str) -> HashTable:
    T = HashTable()

    crawled = await crawl(root)
    saved_nodes = []
    for i in crawled.nodes:
        saved_nodes.append(CrawledNodeToNode(i))

    for i in saved_nodes:
        T.insert(i)
    return T

def CrawledNodeToNode(to_convert: CrawledNode) -> Node:
    # print(f"url: {to_convert.at} parent: {to_convert.parent} children: {to_convert.children}")
    # TO DO : use Node.addChild instead of direct assignment
    return Node(to_convert.at, to_convert.parent, to_convert.children, to_convert.indexed, to_convert.html_metadata)

# This is currently a simple version of this. it answers the question: "do we need to make a new history entry?". the answer is YES if nodes have been added, deleted, changed, or are offline

async def compareState(base:dict):
    CHANGEFLAG = 0
    OldTable = HashTable()
    OldTable.fromData(base)
    start = time.time()
    NewTable = await read_chain_into_table('https://webchain.milkmedicine.net')
    end = time.time()
    NewTable.setStart(datetime.fromtimestamp(start, tz=timezone.utc).isoformat())
    NewTable.setEnd(datetime.fromtimestamp(end, tz=timezone.utc).isoformat())

    # print("======= OLD TABLE =======")
    # OldTable.view()
    # print("======= NEW TABLE =======")
    # NewTable.view()

    # check if nodes have been added or deleted
    if len(NewTable.table) != len(OldTable.table):
        # either node has been added or deleted. this means time to make a new state
        CHANGEFLAG = 1

    # compare new nodes to old table
    changed_nodes = []
    for l in NewTable.table:
        for i in l:
            result = nodeCompare(i, OldTable)
            if result != [0,0,0]:
                # if something changed even once, we know time to make a new state
                CHANGEFLAG = 1
                changed_nodes.append(i)

    if CHANGEFLAG:
        # save it as current
        Serialize(NewTable, "current")
        # log old table as timestamped ver
        # to do: process name better
        Serialize(OldTable, f"v{OldTable.end}")
    return CHANGEFLAG

# nodeCompare
# return codes:
# retList is of the form [a, b, c], where
# a is an int or list of the indexes of the crawled node's children that have been changed
# b is 1 if the parent is changed, or 0 otherwise
# c is 0 if the crawled node is online, and previously also was, or is offline and previously also was (I.e no change)
#   is 1 if the crawled node was online and is now offline
#   is 2 if the crawled node was offline and is now online again
# EXCEPT if the crawled node is not in the old table, then it is a new node and retList is [-1,-1,-1]

def nodeCompare(n1:Node, oldTable: HashTable):
    retList = [0,0,0]
    CONSTANTFLAG = 0
    n2 = oldTable.findValueByURL(n1.url)
    print(f"n1: {n1}")
    # This means node did not exist in old table (i.e new node).
    #
    if n2 == -1:
        print ("BINGUS")
        return [-1,-1,-1]
    # else Node DID exist in old table, confirm that parents/children are same, and that indexed = true in new one.
    else:
        print(f"n2: {n2}")
        ChangedChildren = []
        for i in n1.children:
            if i not in n2.children:
                print(f"{i} not in list {n2.children}")
                #returns position of child thats changed
                ChangedChildren.append(n1.children.index(i))
                retList[0] = ChangedChildren
            else:
                retList[0] = 0
        # this could happen if the site is dropped by original parent but picked up by different one
        if n1.parent != n2.parent:
            retList[1] = 1
        # i.e is it offline / unreachable now but wasnt in past
        if n1.indexed == False and n2.indexed == True:
            retList[2] = 1
        # i.e is it offline / unreachable in past but online now
        if (n1.indexed == True and n2.indexed == False):
            retList[2] = 2
        return retList


# These use log() and fromData() to maintain compliance with crawl()
def Serialize(T:HashTable, filename:str|None = None):
    if filename:
        with open(f'../web/static/crawler/{filename}.json','w') as f:
            jjson.dump(T.log(),f)
    else:
        with open(f'../web/static/crawler/table.json','w') as f:
            jjson.dump(T.log(),f)
    return

def Deserialize(filename: str|None = None) -> HashTable:
    T = HashTable()
    if filename:
        with open(f'../web/static/crawler/{filename}.json','r') as f:
            T.fromData(jjson.load(f))
    else:
        with open(f'../web/static/crawler/table.json','r') as f:
            T.fromData(jjson.load(f))
    return T
