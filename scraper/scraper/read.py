from scraper.crawl import CrawlResponse, CrawledNode
import logging

logger = logging.getLogger()


# This is currently a simple version of this. it answers the question: "do we need to make a new history entry?". the answer is YES if nodes have been added, deleted, changed, or are offline
# In the future, I would like to improve this so that we are logging WHAT changes are being made
async def compareState(
    response_1: CrawlResponse, response_2: CrawlResponse
) -> CrawlResponse | None:
    """
    Compare two CrawlResponse objects and detect changes.
    Returns a log (list of changed nodes) if changes are detected, otherwise None.
    """
    CHANGEFLAG = 0

    if response_1.end >= response_2.end:
        old_response = response_2
        new_response = response_1
    else:
        old_response = response_1
        new_response = response_2

    # check if nodes have been added or deleted
    if len(new_response.nodes) != len(old_response.nodes):
        CHANGEFLAG = 1

    # Helper to find node by 'at' in a node list
    def find_node(nodes, at):
        for idx, node in enumerate(nodes):
            logger.info(f"FINDNODE: {idx} : {node}\n")
            if node.at == at:
                return idx
        return -1

    changed_nodes = []
    mark_not_indexed = []
    for i in new_response.nodes:
        if i.indexed == False:
            mark_not_indexed.append(i.at)
        if i in mark_not_indexed:
            continue
        else:
            old_node_index = find_node(old_response.nodes, i.at)
            old_node = old_response.nodes[old_node_index] if old_node_index != -1 else -1
            result = nodeCompare(i, old_node)
            # Only set first_seen if None (do not overwrite)
            if result == [-1,-1,-1]:
                i.first_seen = new_response.end
            if result[2] == -2:
                i.first_seen = old_response.end
            if result[2] == -3:
                i.first_seen = old_node.first_seen
            # Update last_updated only if node has changed
            if result != [0, 0, 0] and result != [0, 0, 0, []]:
                if len(result) > 3:
                    for x in result[3]:
                        mark_not_indexed.append(x)
                i.last_updated = new_response.end
                CHANGEFLAG = 1
                logger.info(f'Change detected at {i}\n')
                changed_nodes.append(i)

    for i in mark_not_indexed:
        idx = find_node(new_response.nodes, i)
        ## If parent, update data
        if idx != -1:
            new_response.nodes[idx].indexed = False
            oidx = find_node(old_response.nodes, i)
            if oidx != -1:
                old_node = old_response.nodes[oidx]
                new_response.nodes[idx].children = old_node.children
                new_response.nodes[idx].unqualified = old_node.unqualified
                for c in old_node.children:
                    mark_not_indexed.append(c)
        #If Subtree, carry over old data, mark as not indexed
        else:
            oidx = find_node(old_response.nodes, i)
            if oidx != -1:
                temp_node = old_response.nodes[oidx]
                for c in temp_node.children:
                    mark_not_indexed.append(c)
                temp_node.indexed = False
                new_response.nodes.append(temp_node)


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
        if not old_node.first_seen:
            retList[2] = -2
        else:
            retList[2] = -3
        ChangedChildren = []
        for i in new_node.children:
            if i not in old_node.children:
                # returns position of child thats changed
                ChangedChildren.append(new_node.children.index(i))
                retList[0] = ChangedChildren
            else:
                retList[0] = 0
        # this could happen if the site is dropped by original parent but picked up by different one
        if new_node.parent != old_node.parent:
            retList[1] = 1

        if new_node.indexed == False:
            retList.append(new_node.children)

        return retList
