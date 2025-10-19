import dataclasses
from typing import Set
from spider.crawl import CrawlResponse, CrawledNode
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
    METADATA_MODIFIED = 1 << 7


def copy_offline_subtree(at: str, visited: Set[str], old_nodes_by_at) -> list[CrawledNode]:
    # copy offline subtree from old crawl
    if at in visited or at not in old_nodes_by_at:
        return []
    visited.add(at)
    old_node = old_nodes_by_at[at]
    node_copy = dataclasses.replace(old_node, indexed=False)
    nodes = [node_copy]
    for child_at in old_node.children:
        nodes.extend(copy_offline_subtree(child_at, visited, old_nodes_by_at))
    return nodes


def sort_nodes_by_hierarchy(nodes: list[CrawledNode]) -> list[CrawledNode]:
    # sort nodes by parent/child relationships, parents before children
    at_to_node = {node.at: node for node in nodes}
    visited = set()
    ordered = []

    def visit(node):
        # visit node and its children in order
        if node.at in visited:
            return
        visited.add(node.at)
        ordered.append(node)
        # visit children in the order listed in the parent's children field
        for child_at in getattr(node, "children", []):
            child = at_to_node.get(child_at)
            if child:
                visit(child)

    # only start from the root(s) as defined by depth==0 (not all parent=none)
    roots = [node for node in nodes if getattr(node, "depth", 0) == 0]
    for root in roots:
        visit(root)
    # add any disconnected nodes (not reachable from roots)
    # this shouldn't really happen, but whatever
    for node in nodes:
        if node.at not in visited:
            visit(node)
    return ordered


def compare_nodes(old_node: CrawledNode | None, new_node: CrawledNode | None) -> NodeChangeMask:
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
    if hasattr(new_node, "unqualified") and hasattr(old_node, "unqualified"):
        if new_node.unqualified != old_node.unqualified:
            mask |= NodeChangeMask.UNQUALIFIED_MODIFIED
    # check for metadata changes: html_metadata, first_seen, last_updated
    # only set METADATA_MODIFIED if both old and new have a value and they differ
    if (
        hasattr(new_node, "html_metadata")
        and hasattr(old_node, "html_metadata")
        and new_node.html_metadata is not None
        and old_node.html_metadata is not None
        and new_node.html_metadata != old_node.html_metadata
    ):
        mask |= NodeChangeMask.METADATA_MODIFIED
    # only set for first_seen if both are not None and differ
    if (
        getattr(new_node, "first_seen", None) is not None
        and getattr(old_node, "first_seen", None) is not None
        and new_node.first_seen != old_node.first_seen
    ):
        mask |= NodeChangeMask.METADATA_MODIFIED
    # only set for last_updated if both are not None and differ
    if (
        getattr(new_node, "last_updated", None) is not None
        and getattr(old_node, "last_updated", None) is not None
        and new_node.last_updated != old_node.last_updated
    ):
        mask |= NodeChangeMask.METADATA_MODIFIED

    return mask


def patch_state(old_response: CrawlResponse, new_response: CrawlResponse) -> CrawlResponse | None:
    """
    patch the new crawl state with offline subtrees and metadata from the old crawl.
    """
    # build lookup tables for fast access
    old_nodes_by_at = {node.at: node for node in old_response.nodes}
    new_nodes_by_at = {node.at: node for node in new_response.nodes}

    # 1. for each node in new crawl that is not indexed, copy its subtree from old crawl
    present_ats = {node.at for node in new_response.nodes}
    offline_visited = set()
    for node in list(new_response.nodes):
        if not node.indexed and node.at in old_nodes_by_at:
            old_node = old_nodes_by_at[node.at]
            # restore children if missing
            if not node.children:
                node.children = old_node.children.copy()
            # copy missing children subtrees
            for child_at in old_node.children:
                if child_at not in present_ats:
                    for subnode in copy_offline_subtree(child_at, offline_visited, old_nodes_by_at):
                        if subnode.at not in present_ats:
                            new_response.nodes.append(subnode)
                            present_ats.add(subnode.at)
                            new_nodes_by_at[subnode.at] = subnode

    # 2. copy metadata from old node onto new node, if not present
    for node in new_response.nodes:
        old_node = old_nodes_by_at.get(node.at)
        if old_node:
            if getattr(node, "first_seen", None) is None:
                node.first_seen = old_node.first_seen
            if getattr(node, "last_updated", None) is None:
                node.last_updated = old_node.last_updated
            if getattr(node, "html_metadata", None) is None:
                node.html_metadata = old_node.html_metadata

    # 3. update last_updated if applicable
    change_detected = False
    for at in set(old_nodes_by_at) | set(new_nodes_by_at):
        old_node = old_nodes_by_at.get(at)
        new_node = new_nodes_by_at.get(at)
        mask = compare_nodes(old_node, new_node)
        if mask != NodeChangeMask.NONE:
            logger.debug(f"{at}: {mask!r}")

        if mask & (
            NodeChangeMask.ADDED
            | NodeChangeMask.REMOVED
            | NodeChangeMask.PARENT_MODIFIED
            | NodeChangeMask.CHILDREN_MODIFIED
            | NodeChangeMask.OFFLINE_TO_ONLINE
            | NodeChangeMask.ONLINE_TO_OFFLINE
            | NodeChangeMask.UNQUALIFIED_MODIFIED
            # do not trigger patch for METADATA_MODIFIED alone
        ):
            if new_node:
                new_node.last_updated = new_response.end
            change_detected = True

    # 4. remove nodes if neither present nor referenced as a child and have no tracked children
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
                logger.info(f"node removed {at}")
        else:
            node = new_nodes_by_at.get(at)
            if node and node.parent:
                parent = new_nodes_by_at.get(node.parent)
                if parent and at not in parent.children:
                    removed_ats.add(at)
                    logger.info(f"node removed (parent no longer lists as child): {at}")
    new_response.nodes = [node for node in new_response.nodes if node.at not in removed_ats]

    # 5. sort nodes by parent/child relationships, parents before children
    new_response.nodes = sort_nodes_by_hierarchy(new_response.nodes)

    # 6. ensure first_seen is set
    for node in new_response.nodes:
        if getattr(node, "first_seen", None) is None:
            node.first_seen = new_response.end

    if change_detected:
        return CrawlResponse(
            start=new_response.start,
            end=new_response.end,
            nodes=new_response.nodes,
            nominations_limit=new_response.nominations_limit,
        )
    return None
