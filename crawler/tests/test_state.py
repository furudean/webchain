import dataclasses
from spider.state import patch_state, compare_nodes, NodeChangeMask
from spider.crawl import CrawlResponse, CrawledNode
import pytest

from spider.contracts import HtmlMetadata
import random
import copy


def test_compare_node_added():
    old = None
    new = CrawledNode(
        at="http://node",
        children=[],
        parent=None,
        indexed=True,
        first_seen=None,
        depth=0,
    )

    mask = compare_nodes(old, new)

    assert mask == NodeChangeMask.ADDED


def test_node_removed():
    old = CrawledNode(
        at="http://node",
        children=[],
        parent=None,
        indexed=True,
        first_seen=None,
        depth=0,
    )
    new = None

    mask = compare_nodes(old, new)

    assert mask == NodeChangeMask.REMOVED


def test_compare_no_change():
    old = CrawledNode(
        at="http://node",
        children=[],
        parent=None,
        indexed=True,
        first_seen=None,
        depth=0,
    )
    new = CrawledNode(
        at="http://node",
        children=[],
        parent=None,
        indexed=True,
        first_seen=None,
        depth=0,
    )

    mask = compare_nodes(old, new)

    assert mask == NodeChangeMask.NONE


def test_ignore_untracked_fields():
    old = CrawledNode(
        at="http://node",
        children=[],
        parent=None,
        indexed=True,
        first_seen=None,
        depth=0,
        unqualified=[],
    )
    new = CrawledNode(
        at="http://node",
        children=[],
        parent=None,
        indexed=True,
        first_seen="2023-01-01T00:00:00Z",
        depth=1,
        unqualified=[],
    )

    mask = compare_nodes(old, new)

    assert mask == NodeChangeMask.NONE


def test_compare_children_modified():
    old = CrawledNode(
        at="http://node",
        children=["http://child1"],
        parent=None,
        indexed=True,
        first_seen=None,
        depth=0,
    )
    new = CrawledNode(
        at="http://node",
        children=["http://child1", "http://child2"],
        parent=None,
        indexed=True,
        first_seen=None,
        depth=0,
    )

    mask = compare_nodes(old, new)

    assert mask == NodeChangeMask.CHILDREN_MODIFIED


def test_compare_parent_changed():
    old = CrawledNode(
        at="http://node",
        children=[],
        parent="http://oldparent",
        indexed=True,
        first_seen=None,
        depth=0,
    )
    new = CrawledNode(
        at="http://node",
        children=[],
        parent="http://newparent",
        indexed=True,
        first_seen=None,
        depth=0,
    )

    mask = compare_nodes(old, new)

    assert mask == NodeChangeMask.PARENT_MODIFIED


def test_compare_offline_to_online():
    old = CrawledNode(
        at="http://node",
        children=[],
        parent=None,
        indexed=False,
        first_seen=None,
        depth=0,
    )
    new = CrawledNode(
        at="http://node",
        children=[],
        parent=None,
        indexed=True,
        first_seen=None,
        depth=0,
    )

    mask = compare_nodes(old, new)

    assert mask == NodeChangeMask.OFFLINE_TO_ONLINE


def test_compare_online_to_offline():
    old = CrawledNode(
        at="http://node",
        children=[],
        parent=None,
        indexed=True,
        first_seen=None,
        depth=0,
    )
    new = CrawledNode(
        at="http://node",
        children=[],
        parent=None,
        indexed=False,
        first_seen=None,
        depth=0,
    )

    mask = compare_nodes(old, new)

    assert mask == NodeChangeMask.ONLINE_TO_OFFLINE


def test_compare_unqualified_change():
    old = CrawledNode(
        at="http://node",
        children=[],
        parent=None,
        indexed=True,
        first_seen=None,
        depth=0,
        unqualified=[],
    )
    new = CrawledNode(
        at="http://node",
        children=[],
        parent=None,
        indexed=True,
        first_seen=None,
        depth=1,
        unqualified=["http://somenode"],
    )

    mask = compare_nodes(old, new)

    assert mask == NodeChangeMask.UNQUALIFIED_MODIFIED


def test_compare_multiple_changes():
    old = CrawledNode(
        at="http://node",
        children=["http://child1"],
        parent="http://oldparent",
        indexed=False,
        first_seen=None,
        depth=0,
    )
    new = CrawledNode(
        at="http://node",
        children=["http://child1", "http://child2"],
        parent="http://newparent",
        indexed=True,
        first_seen=None,
        depth=0,
    )

    mask = compare_nodes(old, new)

    assert mask & NodeChangeMask.CHILDREN_MODIFIED
    assert mask & NodeChangeMask.PARENT_MODIFIED
    assert mask & NodeChangeMask.OFFLINE_TO_ONLINE
    assert mask != NodeChangeMask.ONLINE_TO_OFFLINE
    assert mask != NodeChangeMask.NONE


def test_compare_metadata_changed_html_metadata(seed_node: CrawledNode):
    old = dataclasses.replace(
        seed_node,
        first_seen="2023-01-01T00:00:00Z",
        last_updated="2023-01-01T00:00:00Z",
        html_metadata=HtmlMetadata(title="Old Title", description="Old Desc", theme_color=None),
    )
    new = dataclasses.replace(
        seed_node,
        first_seen="2023-01-01T00:00:00Z",
        last_updated="2023-01-01T00:00:00Z",
        html_metadata=HtmlMetadata(title="New Title", description="Old Desc", theme_color=None),
    )

    mask = compare_nodes(old, new)

    assert mask == NodeChangeMask.METADATA_MODIFIED


def test_compare_metadata_changed_first_seen(seed_node: CrawledNode):
    old = dataclasses.replace(
        seed_node,
        first_seen="2023-01-01T00:00:00Z",
        last_updated="2023-01-01T00:00:00Z",
    )
    new = dataclasses.replace(
        seed_node,
        first_seen="2023-01-02T00:00:00Z",
        last_updated="2023-01-01T00:00:00Z",
    )

    mask = compare_nodes(old, new)

    assert mask == NodeChangeMask.METADATA_MODIFIED


def test_compare_metadata_changed_last_updated(seed_node: CrawledNode):
    old = dataclasses.replace(
        seed_node,
        first_seen="2023-01-01T00:00:00Z",
        last_updated="2023-01-01T00:00:00Z",
    )
    new = dataclasses.replace(
        seed_node,
        first_seen="2023-01-01T00:00:00Z",
        last_updated="2023-01-02T00:00:00Z",
    )

    mask = compare_nodes(old, new)

    assert mask == NodeChangeMask.METADATA_MODIFIED


def test_compare_metadata_no_change(seed_node: CrawledNode):
    old = dataclasses.replace(
        seed_node,
        first_seen="2023-01-01T00:00:00Z",
        last_updated="2023-01-01T00:00:00Z",
        html_metadata=HtmlMetadata(title="Title", description="Desc", theme_color=None),
    )
    new = dataclasses.replace(
        seed_node,
        first_seen="2023-01-01T00:00:00Z",
        last_updated="2023-01-01T00:00:00Z",
        html_metadata=HtmlMetadata(title="Title", description="Desc", theme_color=None),
    )

    mask = compare_nodes(old, new)

    assert mask == NodeChangeMask.NONE


@pytest.fixture
def old_crawl():
    return CrawlResponse(
        nodes=[],
        start="1995-01-01T00:00:00Z",
        end="1995-01-01T00:05:00Z",
        nominations_limit=4,
    )


@pytest.fixture
def new_crawl():
    return CrawlResponse(
        nodes=[],
        start="2000-01-01T00:10:00Z",
        end="2000-01-01T00:15:00Z",
        nominations_limit=4,
    )


@pytest.fixture
def seed_node():
    return CrawledNode(
        at="http://node",
        children=[],
        parent=None,
        indexed=True,
        depth=0,
    )


def test_patch_added(old_crawl: CrawlResponse, new_crawl: CrawlResponse, seed_node: CrawledNode):
    new_crawl.nodes = [seed_node]

    patched = patch_state(old_crawl, new_crawl)

    assert patched is not None
    expected_node = dataclasses.replace(
        seed_node,
        first_seen=new_crawl.end,
        last_updated=new_crawl.end,
    )
    assert patched.nodes == [expected_node]
    assert patched.start == new_crawl.start
    assert patched.end == new_crawl.end


def test_patch_no_op(old_crawl: CrawlResponse, new_crawl: CrawlResponse, seed_node: CrawledNode):
    old_crawl.nodes = [seed_node]
    new_crawl.nodes = [seed_node]

    patched = patch_state(old_crawl, new_crawl)

    assert patched is None


def test_patch_node_removed(
    old_crawl: CrawlResponse, new_crawl: CrawlResponse, seed_node: CrawledNode
):
    old_crawl.nodes = [seed_node]
    new_crawl.nodes = []

    patched = patch_state(old_crawl, new_crawl)

    assert patched is not None
    assert patched.nodes == []


def test_node_modified(old_crawl: CrawlResponse, new_crawl: CrawlResponse, seed_node: CrawledNode):
    modified_node = dataclasses.replace(
        seed_node,
        indexed=False,
    )
    old_crawl.nodes = [seed_node]
    new_crawl.nodes = [modified_node]

    patched = patch_state(old_crawl, new_crawl)

    assert patched is not None
    assert len(patched.nodes) == 1
    assert patched.nodes[0].indexed == modified_node.indexed
    assert patched.nodes[0].last_updated == new_crawl.end


def test_patch_child_added(
    old_crawl: CrawlResponse, new_crawl: CrawlResponse, seed_node: CrawledNode
):
    child_node = dataclasses.replace(
        seed_node,
        at="http://child",
        parent=seed_node.at,
        depth=1,
    )
    old_crawl.nodes = [seed_node]
    new_crawl.nodes = [
        dataclasses.replace(
            seed_node,
            children=[child_node.at],
        ),
        child_node,
    ]

    patched = patch_state(old_crawl, new_crawl)

    assert patched is not None
    assert len(patched.nodes) == 2


def test_child_removed(old_crawl: CrawlResponse, new_crawl: CrawlResponse, seed_node: CrawledNode):
    child_node = dataclasses.replace(
        seed_node,
        at="http://child",
        parent=seed_node.at,
        depth=1,
    )
    old_crawl.nodes = [
        dataclasses.replace(
            seed_node,
            children=[child_node.at],
        ),
        child_node,
    ]
    new_crawl.nodes = [seed_node]

    patched = patch_state(old_crawl, new_crawl)

    assert patched is not None
    assert len(patched.nodes) == 1


def test_patch_offline_subtree(old_crawl: CrawlResponse, new_crawl: CrawlResponse):
    child_node = CrawledNode(
        at="http://child",
        children=["http://grandchild"],
        parent="http://node",
        indexed=True,
        depth=1,
    )
    grandchild_node = CrawledNode(
        at="http://grandchild",
        children=[],
        parent="http://child",
        indexed=True,
        depth=2,
    )
    old_crawl.nodes = [
        CrawledNode(
            at="http://node",
            children=["http://child"],
            parent=None,
            indexed=True,
            depth=0,
        ),
        child_node,
        grandchild_node,
    ]
    new_crawl.nodes = [
        CrawledNode(
            at="http://node",
            children=[],
            parent=None,
            indexed=False,
            depth=0,
        ),
    ]

    patched = patch_state(old_crawl, new_crawl)

    assert patched is not None
    assert len(patched.nodes) == 3
    ats = {node.at for node in patched.nodes}
    assert "http://child" in ats
    assert "http://grandchild" in ats
    assert all(not node.indexed for node in patched.nodes if node.at != "http://node")


def test_logical_order(old_crawl: CrawlResponse, new_crawl: CrawlResponse):
    seed_node = CrawledNode(
        at="http://seed",
        children=["http://has_children", "http://unrelatednode"],
        parent=None,
        indexed=True,
        depth=0,
    )

    unrelated_node = CrawledNode(
        at="http://unrelatednode",
        children=[],
        parent="http://seed",
        indexed=True,
        depth=1,
    )

    children = [
        CrawledNode(
            at=f"http://child{i}",
            children=[],
            parent="http://has_children",
            indexed=True,
            depth=2,
        )
        for i in range(3)
    ]

    parent_node = CrawledNode(
        at="http://has_children",
        children=[child.at for child in children],
        parent=None,
        indexed=True,
        depth=1,
    )

    sorted_nodes = [seed_node, parent_node, *children]
    old_crawl.nodes = sorted_nodes.copy()
    new_crawl.nodes = sorted_nodes.copy() + [unrelated_node]
    random.seed(42)
    random.shuffle(new_crawl.nodes)

    patched = patch_state(old_crawl, new_crawl)

    assert patched is not None

    # All nodes should have first_seen set to new_crawl.end, and unrelated_node also gets last_updated
    expected_nodes = [
        dataclasses.replace(node, first_seen=new_crawl.end) for node in sorted_nodes
    ] + [
        dataclasses.replace(
            unrelated_node,
            first_seen=new_crawl.end,
            last_updated=new_crawl.end,
        )
    ]
    assert patched.nodes == expected_nodes


def test_pick_up_new_metadata(
    old_crawl: CrawlResponse, new_crawl: CrawlResponse, seed_node: CrawledNode
):
    old_crawl.nodes = [seed_node]
    new_node = dataclasses.replace(
        seed_node,
        first_seen="2000-01-01T00:00:00Z",
        last_updated="2000-01-01T00:05:00Z",
        html_metadata=HtmlMetadata(
            title="New Title", description="New Description", theme_color=None
        ),
    )
    unrelated_node = dataclasses.replace(
        seed_node,
        at="http://othernode",
    )
    new_crawl.nodes = [new_node, unrelated_node]

    patched = patch_state(old_crawl, new_crawl)

    assert patched is not None
    assert len(patched.nodes) == 2
    assert patched.nodes[0].html_metadata is not None
    assert patched.nodes[0].html_metadata.title == "New Title"
    assert patched.nodes[0].first_seen == "2000-01-01T00:00:00Z"
    assert patched.nodes[0].last_updated == "2000-01-01T00:05:00Z"


def test_preserve_missing_metadata(
    old_crawl: CrawlResponse, new_crawl: CrawlResponse, seed_node: CrawledNode
):
    metadata_node = dataclasses.replace(
        seed_node,
        first_seen="1995-01-01T00:02:00Z",
        last_updated="1995-01-05T00:01:00Z",
        html_metadata=dataclasses.replace(
            seed_node.html_metadata or HtmlMetadata(None, None, None),
            title="Old Title",
        ),
    )
    # unrelated node to make sure that a state is returned
    unrelated_node = dataclasses.replace(
        seed_node,
        at="http://othernode",
    )

    old_crawl.nodes = [metadata_node, unrelated_node]
    new_crawl.nodes = [seed_node]

    patched = patch_state(old_crawl, new_crawl)

    assert patched is not None
    assert len(patched.nodes) == 1
    assert patched.nodes[0].html_metadata is not None
    assert patched.nodes[0].html_metadata.title == "Old Title"
    assert patched.nodes[0].first_seen == "1995-01-01T00:02:00Z"
    assert patched.nodes[0].last_updated == "1995-01-05T00:01:00Z"


def test_irrelevant_changes(
    old_crawl: CrawlResponse, new_crawl: CrawlResponse, seed_node: CrawledNode
):
    old_node = dataclasses.replace(
        seed_node, last_updated="1995-01-01T00:00:00Z", html_metadata=None
    )
    new_node = dataclasses.replace(
        seed_node,
        last_updated="2000-01-01T00:00:00Z",
        html_metadata=HtmlMetadata(
            title="New Title", description="New Description", theme_color=None
        ),
    )

    old_crawl.nodes = [old_node]
    new_crawl.nodes = [new_node]

    patched = patch_state(old_crawl, new_crawl)

    assert patched is None


def test_children_modified(
    old_crawl: CrawlResponse, new_crawl: CrawlResponse, seed_node: CrawledNode
):
    old_node = dataclasses.replace(
        seed_node,
        children=[],
    )
    new_node = dataclasses.replace(
        old_node,
        children=["http://child1", "http://child2"],
    )
    child_1 = dataclasses.replace(
        seed_node,
        at="http://child1",
        parent=seed_node.at,
        depth=1,
    )
    child_2 = dataclasses.replace(
        seed_node,
        at="http://child2",
        parent=seed_node.at,
        depth=1,
    )

    old_crawl.nodes = [old_node]
    new_crawl.nodes = [new_node, child_1, child_2]

    patched = patch_state(old_crawl, new_crawl)

    assert patched is not None
    assert len(patched.nodes) == 3

    # All nodes should have first_seen and last_updated set to new_crawl.end
    expected_nodes = [
        dataclasses.replace(
            new_node,
            first_seen=new_crawl.end,
            last_updated=new_crawl.end,
        ),
        dataclasses.replace(
            child_1,
            first_seen=new_crawl.end,
            last_updated=new_crawl.end,
        ),
        dataclasses.replace(
            child_2,
            first_seen=new_crawl.end,
            last_updated=new_crawl.end,
        ),
    ]
    assert patched.nodes == expected_nodes


def test_patch_state_immutability(
    old_crawl: CrawlResponse, new_crawl: CrawlResponse, seed_node: CrawledNode
):
    old_crawl.nodes = [seed_node]
    new_node = dataclasses.replace(seed_node, indexed=False)
    new_crawl.nodes = [new_node]

    old_crawl_copy = copy.deepcopy(old_crawl)
    new_crawl_copy = copy.deepcopy(new_crawl)

    patch_state(old_crawl, new_crawl)

    assert old_crawl == old_crawl_copy
    assert new_crawl == new_crawl_copy
