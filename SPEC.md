# webchain Specification (draft)

webchain is a distributed [webring](https://en.wikipedia.org/wiki/Webring),
where each member can nominate other websites, creating a walkable graph of
trust.

In webchain, each member nominates others to the chain, who get their own
nominations in turn. This creates a tree-like structure, where each node has a
parent and potentially children.

The size of the webchain is not fixed, and is only limited by the half-life of
the internet. A node may disappear from the webchain, taking with it all of its
nominations. This is not a bug.

Each node has a responsibility to ensure that its children are trustworthy and
don't abuse the system. If a member or its dependents are found to be abusive,
they can be removed from the webchain by members terminating their nomination
higher up the chain.

## Rules

1. The tree starts with a single node, for example: https://mychain.org.
2. Each node in the tree represents a website, which is identified by its URL.
3. Each node may define child nominations by including appropriate `<link>` tags
   in the `<head>` section of its HTML (see examples below).
4. Each node can nominate up to 3 other nodes, with any additional nominations
   being ignored. Nominations may be freely added or removed by the node owner,
   at their discretion.
5. A nominated node can be any valid URL, including subdomains, paths, or even
   different domains altogether.
6. Nodes may not nominate themselves or create cycles in the nomination path. If
   these cases are detected, the offending nominations are ignored.
7. If a node does not respond with a 200 status-code in a timely manner, the
   node is considered offline. Offline nodes are still a part of the data
   representation, but its subtree is not traversable until it comes online
   again.

## Example node

```html
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">

	<!-- The root of the webchain this node is part of -->
	<link rel="webchain" href="https://mychain.org">
	<!-- Nominations made by this node -->
	<link rel="webchain-nomination" href="https://www.example.org">
	<link rel="webchain-nomination" href="https://www.wikipedia.org">
</head>
<body>
	example webchain document with two nominations
</body>
</html>
```

In this example, this node has nominated two others: `www.example.org` and
`www.wikipedia.org`. They are now part of the webchain `mychain.org`.

Note that simply adding webchain markup to your site does not automatically make
you part of the webchain - the example must first be nominated by an existing
member.

## Joining a webchain

Let's say you have a website, `https://www.example.org`, and you want to join
the webchain rooted at `https://mychain.org`.

1. Find the webchain root (e.g., `https://mychain.org`) and
	visit it to understand the community and its purpose
2. Request nomination by contacting existing members with open slots, asking
   for a nomination.
3. An existing member can admit you to the webchain by adding
   `<link rel="webchain-nomination" href="https://www.example.org">` tag to
   their page.

The user is now part of the webchain. They may now nominate others by adding
markup to their own page.

## Crawling

Webchain is intended to be crawled from the root node. The crawler should start
from the root URL, fetch the HTML content, and parse it to extract nominations.

Assuming the nominations are valid (not breaking any of the stated
[rules](#rules)), the crawler should then recursively visit each nominated URL,
fetch its content, and extract further nominations until all paths are
exhausted. It may be useful to keep track of visited URLs to avoid cycles.

The crawler should also handle errors gracefully, such as timeouts or invalid
responses, and skip over any nodes that cannot be reached.

It may be of interest to store metadata over time about each node, such as its
join time, last seen time, and nomination history so that the evolution of the
graph can be studied.

## A note on visibility

The webchain isn't very fun on its own. Visualization software will have to be
created to traverse the graph and display it in a meaningful way. This includes
handling of historical states, offline nodes, and other metadata.

The webchain root should be treated as a starting point for discovering the
rest of the chain. A web page or application should be created to visualize the
chain and allow users to navigate it.

Discoverability may be an issue, as visitors of any given node will have to know
the webchain exists to browse it. Users should thus be encouraged to link back
to the webchain root node or other representations available.

If all parts work well together, a fun and dangerous social experiment will
emerge.


## Concerns

Since a nomination URL can be any valid URL, it is possible for a single actor
to create a large number of nodes and nominate each other. Since the webchain is
based on trust, such an attack is not likely to succeed unless the attacker can
convince existing members to nominate them.

If a nominated domain expires and is purchased by a malicious actor, they
inherit the trust relationship and position in the webchain without the original
vetting process.

With each node limited to 2 nominations, the webchain could become unable to
grow if the edges don't invite new nodes. This could be mitigated by allowing
more nominations per node, but that would also increase the risk of abuse.

With the current design, members may only be in one webchain at a time. This is
a deliberate choice to keep things simple. Allowing multiple webchains would
increase markup and crawler complexity.
