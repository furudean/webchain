# webchain Specification (draft)

webchain is a decentralized [webring](https://en.wikipedia.org/wiki/Webring),
where each website can nominate other websites to create a walkable graph of
trust.

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
7. Each node can nominate up to 3 other nodes, with any additional nominations
   being ignored.
8. The DAG must not contain cycles, meaning that nodes may not nominate a node
   that is already a part of the graph. If any such relationship is found, it is
   ignored.

## Example node

```html
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">

	<meta name="webchain-nomination" content="www.himawari.fun">
	<meta name="webchain-nomination" content="eidoli.ca">
	<meta name="webchain-nomination" content="nekopath.fun">
</head>
<body>
	example webchain document with two nominations
</body>
</html>
```

In this example, the node has nominated two other nodes: `www.himawari.fun` and
`eidoli.ca`.
