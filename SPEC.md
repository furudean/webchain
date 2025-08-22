# webchain Specification (draft)

webchain is a decentralized [webring](https://en.wikipedia.org/wiki/Webring),
where each member website can nominate other websites, creating a walkable graph
of trust.

Each member can nominate new members, who in turn can invite members. Each node
has a responsibility to ensure that its nominations are trustworthy and don't
abuse the system. If a member or its dependents are found to be abusive, it can
be removed from the webchain by terminating a nomination.

The size of the webchain is not fixed, and is only limited by the half-life of
the internet. A node may disappear from the webchain, taking with it all of its
nominations. This is not a bug.

## Rules

1. The DAG starts with a single root node, for example:
   https://chain.milkmedicine.net.
2. Each node in the DAG represents a website, which is identified by its URL.
3. Each node can define edges to other nodes by including a `<meta>` tag in the
   `<head>` section of its HTML.
4. The `<meta>` tag should have the attribute `name="webchain-nomination"` and
   the attribute `content` set to the URL of the node it nominates.
5. A nominated node can be any valid URL that is not itself.
6. Each node can nominate up to 2 other nodes, with any additional nominations
   being ignored.
7. The DAG must not contain cycles, meaning that nodes may not nominate a node
   that is already a part of the graph. If any such relationship is found, it is
   ignored.
8. If a node does not respond with a 200 status code in a timely manner, the
   node is considered offline. Offline nodes are still a part of the data
   representation, but their subtree is not traversable.

## Example node

```html
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">

	<meta name="webchain-nomination" content="https://www.example.org">
	<meta name="webchain-nomination" content="https://www.wikipedia.org">
</head>
<body>
	example webchain document with two nominations
</body>
</html>
```

In this example, the node has nominated three other nodes: `www.example.org`
and `www.wikipedia.org`. They are now part of the webchain.
