# webchain Specification (draft)

webchain is a decentralized [webring](https://en.wikipedia.org/wiki/Webring),
where each member website can nominate other websites, creating a walkable graph
of trust.

In webchain, each member nominates others to the chain, who get their own
nominations in turn. This creates a tree-like structure, where each node has a
parent and potentially children.

The size of the webchain is not fixed, and is only limited by the half-life of
the internet. A node may disappear from the webchain, taking with it all of its
nominations. This is not a bug.

Each node has a responsibility to ensure that its children are trustworthy and
don't abuse the system. If a member or its dependents are found to be abusive,
they can be removed from the webchain by terminating a nomination higher up the
chain.

## Rules

1. The tree starts with a single root node, for example:
   https://chain.milkmedicine.net.
2. Each node in the tree represents a website, which is identified by its URL.
3. Each node can define its child nominations by including appropriate `<link>`
   tags in the `<head>` section of its HTML (see examples below).
4. A nominated node can be any valid URL that is not itself.
5. Each node can nominate up to 2 other nodes, with any additional nominations
   being ignored.
6. Nominations may be freely added or removed by the node owner, at consequence
   of being deemed untrustworthy by the community.
7. The tree must not contain cycles, meaning that nodes may not nominate a node
   that is already a part of the graph. If any such relationship is found, it is
   ignored.
8. If a node does not respond with a 200 status code in a timely manner, the
   node is considered offline. Offline nodes are still a part of the data
   representation, but their subtree is not traversable until they come online
   again.

## Example node

```html
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">

	<link rel="webchain" href="https://chain.milkmedicine.net">
	<link rel="webchain-nomination" href="https://www.example.org">
	<link rel="webchain-nomination" href="https://www.wikipedia.org">
</head>
<body>
	example webchain document with two nominations
</body>
</html>
```

In this example, this node has nominated two others: `www.example.org` and
`www.wikipedia.org`. They are now part of the webchain
`https://chain.milkmedicine.net`.

Of course, the example itself must first nominated by another node to be part of
the chain.

## A note on visibility

The webchain isn't very fun on its own. Visualization software will have to be
created to traverse the graph and display it in a meaningful way. This includes
handling of historical states, offline nodes, and other metadata.

Discoverability may be an issue, as visitors of any given node will have to know
the webchain exists to browse it. Users should thus be encouraged to link back
to the webchain root node or other representations available.

If all parts work well together, a fun and dangerous social experiment will
emerge.
