from scraper.crawl import CrawlResponse, CrawledNode


# This is currently a simple version of this. it answers the question: "do we need to make a new history entry?". the answer is YES if nodes have been added, deleted, changed, or are offline
# In the future, I would like to improve this so that we are logging WHAT changes are being made
async def compareState(resp1: CrawlResponse, resp2: CrawlResponse) -> CrawlResponse | None:
    """
    Compare two CrawlResponse objects and detect changes.
    Returns a log (list of changed nodes) if changes are detected, otherwise None.
    """
    CHANGEFLAG = 0

    # Determine which response is older/newer based on 'end' timestamp
    if resp1.end >= resp2.end:
        old_response = resp2
        new_response = resp1
    else:
        old_response = resp1
        new_response = resp2

    # check if nodes have been added or deleted
    if len(new_response.nodes) != len(old_response.nodes):
        CHANGEFLAG = 1

    # Helper to find node by 'at' in a node list
    def find_node(nodes, at):
        for idx, node in enumerate(nodes):
            if node.at == at:
                return idx
        return -1

    changed_nodes = []
    mark_not_indexed = []
    for i in new_response.nodes:
        if i in mark_not_indexed:
            continue
        else:
            if i.first_seen is None:
                i.first_seen = new_response.end
                i.last_updated = new_response.end
            old_node_index = find_node(old_response.nodes, i.at)
            old_node = old_response.nodes[old_node_index] if old_node_index != -1 else -1
            result = nodeCompare(i, old_node)
            if result != [0, 0, 0] and result != [0, 0, 0, []]:
                if len(result) > 3:
                    for x in result[3]:
                        mark_not_indexed.append(x)
                i.last_updated = new_response.end
                CHANGEFLAG = 1
                changed_nodes.append(i)

    for i in mark_not_indexed:
        idx = find_node(new_response.nodes, i.at)
        if idx != -1:
            new_response.nodes[idx].indexed = False

    if CHANGEFLAG:
        return CrawlResponse(
            start=new_response.start,
            end=new_response.end,
            nodes=new_response.nodes,
            nominations_limit=new_response.nominations_limit,
        )

    return None


# nodeCompare
# return codes:
# retList is of the form [a, b, c], where
# a is an int or list of the indexes of the crawled node's children that have been changed
# b is 1 if the parent is changed, or 0 otherwise
# c is 0 if the crawled node is online, and previously also was, or is offline and previously also was (I.e no change)
#   is 1 if the crawled node was online and is now offline
#   is 2 if the crawled node was offline and is now online again
# EXCEPT if the crawled node is not in the old table, then it is a new node and retList is [-1,-1,-1]
def nodeCompare(new_node: CrawledNode, old_node: CrawledNode) -> list[int]:
    retList = [0, 0, 0]
    # print(f"new: {new_node}")
    # This means node did not exist in old table (i.e new node).
    #
    if old_node == -1:
        # print ("old: NOT FOUND")
        return [-1, -1, -1]
    # else Node DID exist in old table, confirm that parents/children are same, and that indexed = true in new one.
    else:
        # print(f"old: {old_node}")
        ChangedChildren = []
        for i in new_node.children:
            if i not in old_node.children:
                # print(f"{i} not in list {old_node.children}")
                # returns position of child thats changed
                ChangedChildren.append(new_node.children.index(i))
                retList[0] = ChangedChildren
            else:
                retList[0] = 0
        # this could happen if the site is dropped by original parent but picked up by different one
        if new_node.parent != old_node.parent:
            retList[1] = 1

        # if new_node.indexed == False:
        #     retList.append(new_node.children)
        #     if old_node.indexed == True:
        #         # i.e is it offline / unreachable now but wasnt in past
        #         retList[2] = 1
        # # i.e is it offline / unreachable in past but online now
        # if new_node.indexed == True and old_node.indexed == False:
        #     retList[2] = 2

        return retList
