from scraper.crawl import CrawlResponse, CrawledNode


# This is currently a simple version of this. it answers the question: "do we need to make a new history entry?". the answer is YES if nodes have been added, deleted, changed, or are offline
# In the future, I would like to improve this so that we are logging WHAT changes are being made
async def compareState(
    old_response: CrawlResponse, new_response: CrawlResponse
) -> CrawlResponse | None:
    """
    Compare two CrawlResponse objects and detect changes.
    Returns a log (list of changed nodes) if changes are detected, otherwise None.
    """
    CHANGEFLAG = 0

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
        if not i.first_seen:
            i.first_seen = new_response.end
        # Use 'at' for comparison instead of object equality
        if any(i.at == x.at for x in mark_not_indexed):
            continue
        else:
            old_node_index = find_node(old_response.nodes, i.at)
            old_node = old_response.nodes[old_node_index] if old_node_index != -1 else -1
            result = nodeCompare(i, old_node)
            # Update last_updated only if node has changed
            if result != [0, 0, 0] and result != [0, 0, 0, []]:
                if len(result) > 3:
                    # Mark children by 'at' for later processing
                    for x in result[3]:
                        child_idx = find_node(new_response.nodes, x)
                        if child_idx != -1:
                            mark_not_indexed.append(new_response.nodes[child_idx])
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
    if old_node == -1:
        return [-1, -1, -1]
    else:
        ChangedChildren = []
        for i in new_node.children:
            if i not in old_node.children:
                ChangedChildren.append(i)  # Use child 'at' value
        retList[0] = ChangedChildren if ChangedChildren else 0
        if new_node.parent != old_node.parent:
            retList[1] = 1
        # Remove online/offline detection
        # (do not compare new_node.indexed vs old_node.indexed)
        # Detect other field changes (add more checks as needed)
        # Example: if new_node.some_field != old_node.some_field: retList.append('field_changed')
        if ChangedChildren:
            retList.append(ChangedChildren)
        return retList
