import dataclasses
from typing import Set
from scraper.crawl import CrawlResponse, CrawledNode
import logging
from enum import IntFlag

logger = logging.getLogger(__name__)


class NodeChangeMask(IntFlag):
    NONE = 0
    ADDED = 1 << 0
    REMOVED = 1 << 1
    PARENT_MODIFIED = 1 << 2
    CHILDREN_MODIFIED = 1 << 3
    OFFLINE_TO_ONLINE = 1 << 4
    ONLINE_TO_OFFLINE = 1 << 5
    UNQUALIFIED_MODIFIED = 1 << 6


def patch_state(old_response: CrawlResponse, new_response: CrawlResponse) -> CrawlResponse | None:
    """
    Patch the new crawl state with offline subtrees and metadata from the old crawl.
    """
    # Build lookup tables for fast access
    old_nodes_by_at = {node.at: node for node in old_response.nodes}
    new_nodes_by_at = {node.at: node for node in new_response.nodes}

    # 1. Start with the new crawl (already in new_response.nodes)

    # 2. For each node in new crawl that is not indexed, copy its subtree from old crawl
    def copy_offline_subtree(at: str, visited: Set[str]) -> list[CrawledNode]:
        if at in visited or at not in old_nodes_by_at:
            return []
        visited.add(at)
        old_node = old_nodes_by_at[at]
        node_copy = dataclasses.replace(old_node, indexed=False)
        nodes = [node_copy]
        for child_at in old_node.children:
            nodes.extend(copy_offline_subtree(child_at, visited))
        return nodes

    present_ats = {node.at for node in new_response.nodes}
    offline_visited = set()
    for node in list(new_response.nodes):
        if not node.indexed and node.at in old_nodes_by_at:
            old_node = old_nodes_by_at[node.at]
            # Restore children if missing
            if not node.children:
                node.children = old_node.children.copy()
            # Copy missing children subtrees
            for child_at in old_node.children:
                if child_at not in present_ats:
                    for subnode in copy_offline_subtree(child_at, offline_visited):
                        if subnode.at not in present_ats:
                            new_response.nodes.append(subnode)
                            present_ats.add(subnode.at)
                            new_nodes_by_at[subnode.at] = subnode

    # 3. Copy metadata from old node onto new node, except for last_updated
    for node in new_response.nodes:
        old_node = old_nodes_by_at.get(node.at)
        if old_node:
            # Copy metadata fields except last_updated
            node.first_seen = old_node.first_seen
            node.html_metadata = old_node.html_metadata
            node.index_error = old_node.index_error
            node.unqualified = old_node.unqualified.copy()

    # 4. Update last_updated if applicable
    change_detected = False
    for at in set(old_nodes_by_at) | set(new_nodes_by_at):
        old_node = old_nodes_by_at.get(at)
        new_node = new_nodes_by_at.get(at)
        mask = compare_nodes(old_node, new_node)
        if mask != NodeChangeMask.NONE:
            logger.debug(f'{at}: {mask!r}')

        if mask & (
            NodeChangeMask.ADDED
            | NodeChangeMask.REMOVED
            | NodeChangeMask.PARENT_MODIFIED
            | NodeChangeMask.CHILDREN_MODIFIED
            | NodeChangeMask.OFFLINE_TO_ONLINE
            | NodeChangeMask.ONLINE_TO_OFFLINE
            | NodeChangeMask.UNQUALIFIED_MODIFIED
        ):
            if new_node:
                new_node.last_updated = new_response.end
            change_detected = True

    # Remove nodes if neither present nor referenced as a child and have no tracked children
    referenced_children = set()
    for node in new_response.nodes:
        referenced_children.update(node.children)
    for node in old_response.nodes:
        referenced_children.update(node.children)
    final_new_ats = {node.at for node in new_response.nodes}
    all_referenced_ats = final_new_ats | referenced_children
    removed_ats = set()
    for at, old_node in old_nodes_by_at.items():
        if at not in all_referenced_ats:
            tracked_children = [c for c in old_node.children if c in final_new_ats]
            if not tracked_children:
                removed_ats.add(at)
                logger.info(f'Node removed {at}')
        else:
            node = new_nodes_by_at.get(at)
            if node and node.parent:
                parent = new_nodes_by_at.get(node.parent)
                if parent and at not in parent.children:
                    removed_ats.add(at)
                    logger.info(f'Node removed (parent no longer lists as child): {at}')
    new_response.nodes = [node for node in new_response.nodes if node.at not in removed_ats]

    # Ensure first_seen is set
    for node in new_response.nodes:
        if getattr(node, 'first_seen', None) is None:
            node.first_seen = new_response.end

    if change_detected:
        return CrawlResponse(
            start=new_response.start,
            end=new_response.end,
            nodes=new_response.nodes,
            nominations_limit=new_response.nominations_limit,
        )
    return None


def compare_nodes(old_node: CrawledNode | None, new_node: CrawledNode | None) -> NodeChangeMask:
    """
    Compare two nodes and return a NodeChangeMask bitmask value.
    """
    mask = NodeChangeMask.NONE
    if old_node is None:
        mask |= NodeChangeMask.ADDED
        return mask
    if new_node is None:
        mask |= NodeChangeMask.REMOVED
        return mask
    if old_node.indexed and not new_node.indexed:
        mask |= NodeChangeMask.ONLINE_TO_OFFLINE
    if not old_node.indexed and new_node.indexed:
        mask |= NodeChangeMask.OFFLINE_TO_ONLINE
    if new_node.parent != old_node.parent:
        mask |= NodeChangeMask.PARENT_MODIFIED
    if new_node.indexed:
        if set(new_node.children) != set(old_node.children):
            mask |= NodeChangeMask.CHILDREN_MODIFIED
    if hasattr(new_node, 'unqualified') and hasattr(old_node, 'unqualified'):
        if new_node.unqualified != old_node.unqualified:
            mask |= NodeChangeMask.UNQUALIFIED_MODIFIED
    # Add more fields as needed
    return mask
