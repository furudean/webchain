from scraper.crawl import crawl, CrawledNode, HtmlMetadata
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
        T.altInsert(i)
    return T

def CrawledNodeToNode(to_convert: CrawledNode) -> Node:
    # Convert HTMLMetadata class instance to dict
    metadata_dict = {}
    metadata_dict.update({"title" : to_convert.html_metadata.title})
    metadata_dict.update({"description" : to_convert.html_metadata.description })
    metadata_dict.update({"theme_color" : to_convert.html_metadata.theme_color})

    # Make sure all children are unique
    child_list = list(set(to_convert.children))

    return Node(to_convert.at, to_convert.parent, child_list, to_convert.indexed, metadata_dict)


# This is currently a simple version of this. it answers the question: "do we need to make a new history entry?". the answer is YES if nodes have been added, deleted, changed, or are offline
# In the future, I would like to improve this so that we are logging WHAT changes are being made
async def compareState(old:dict):
    CHANGEFLAG = 0

    OldTable = HashTable()
    OldTable.fromData(old)

    # crawl chain anew, save into table
    # could rewrite this to load NewTable from some .json if necessary
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
        Serialize(NewTable, "current.json")

        # log old table as timestamped ver
        # to do: process name better
        # ds = datetime.fromisoformat(OldTable.end)
        # print(f"ds: {ds}")

        Serialize(OldTable, f"{OldTable.end}.json")

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
def nodeCompare(new_node:Node, oldTable: HashTable):
    retList = [0,0,0]
    old_node = oldTable.find(new_node.url)
    print(f"new: {new_node}")
    # This means node did not exist in old table (i.e new node).
    #
    if old_node == -1:
        print ("old: NOT FOUND")
        return [-1,-1,-1]
    # else Node DID exist in old table, confirm that parents/children are same, and that indexed = true in new one.
    else:
        print(f"old: {old_node}")
        ChangedChildren = []
        for i in new_node.children:
            if i not in old_node.children:
                print(f"{i} not in list {old_node.children}")
                #returns position of child thats changed
                ChangedChildren.append(new_node.children.index(i))
                retList[0] = ChangedChildren
            else:
                retList[0] = 0
        # this could happen if the site is dropped by original parent but picked up by different one
        if new_node.parent != old_node.parent:
            retList[1] = 1
        # i.e is it offline / unreachable now but wasnt in past
        if new_node.indexed == False and old_node.indexed == True:
            retList[2] = 1
        # i.e is it offline / unreachable in past but online now
        if (new_node.indexed == True and old_node.indexed == False):
            retList[2] = 2
        return retList


# These use log() and fromData() to maintain compliance with crawl()
def Serialize(T:HashTable, filename:str|None = None) -> str:
    if filename:
        location = filename
        with open(f'../web/static/crawler/{location}','w') as f:
            jjson.dump(T.log(),f)
    else:
        location = 'table.json'
        with open(f'../web/static/crawler/{location}','w') as f:
            jjson.dump(T.log(),f)
    return location

def Deserialize(filename: str|None = None) -> HashTable:
    T = HashTable()
    if filename:
        with open(f'../web/static/crawler/{filename}.json','r') as f:
            T.fromData(jjson.load(f))
    else:
        with open(f'../web/static/crawler/table.json','r') as f:
            T.fromData(jjson.load(f))
    return T
