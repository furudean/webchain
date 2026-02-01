<script lang="ts">
	import { browser } from "$app/environment"
	import { page } from "$app/state"
	import type { DisplayNode } from "$lib/node"

	// Props
	const {
		nodes,
		nominations_limit = -1
	}: {
		nodes: DisplayNode[]
		nominations_limit: number | null
	} = $props()

	let button = $state("/button.png")
	let embed_node: DisplayNode | undefined = $state()

	const snippet = $derived.by(() => {
		const url = new URL(page.url.origin)
		if (embed_node) {
			url.searchParams.set("node", embed_node.url_param)
		} else {
			url.searchParams.delete("node")
		}
		return (
			`<a href="${url}" rel="external">` +
			`<img src="${new URL(button, page.url.origin).href}" style="image-rendering: pixelated;" height="31" width="88"/>` +
			`</a>`
		)
	})
</script>

<details name="qna">
	<summary>webchain?</summary>
	<p>
		A <a href="/doc/spec.md">webchain</a>
		is a distributed
		<a href="https://en.wikipedia.org/wiki/Webring" rel="external">webring</a>,
		where each tracked website can nominate new members, creating a walkable
		graph of trust.
	</p>

	<ol>
		<li>
			This page is the starting point of the <em>milkmedicine webchain</em>,
			which is itself a webchain link. It nominates several other websites in
			its HTML.
		</li>
		<li>
			Nominated websites may add nominations by adding markup to their HTML, up
			to a limit of {nominations_limit}.
		</li>
		<li>
			Those websites may nominate {nominations_limit} others, and so on, and so forth.
		</li>
	</ol>

	<p>
		A crawler visits each link, reads its nominations, and then visits those
		links recursively, building up a graph of all reachable sites. The crawler
		runs periodically, so new links will appear on this page over time.
	</p>
	<p>
		Source code may be found <a
			href="https://github.com/furudean/webchain"
			rel="external">on GitHub</a
		>. The <a href="/doc/spec.md">specification</a> may also be of interest.
	</p>
</details>

<details name="qna">
	<summary>nomination</summary>
	<p>
		To nominate new pages to the webchain, an existing member can add markup to
		its HTML, for example:
	</p>
	<pre><code
			>&lt;-- https://example.org ---&gt;
&lthtml&gt;
&lt;head&gt;
	&lt;link rel="webchain"
		href="{page.url.origin}" /&gt;
	&lt;link rel="webchain-nomination"
		href="https://foo.bar" /&gt;
&lt;/head&gt;
&lt;body&gt;
	...
&lt/body&gt;
&lt/html&gt;</code
		></pre>
	<p>
		This snippet shows the website <code>https://example.org</code>. This site
		nominates
		<code>https://foo.bar</code>
		to be part of the webchain
		<code>{page.url.origin}</code>.
	</p>
	<blockquote>
		The <code>webchain</code> link points to the webchain the website wants to
		be a part of. The
		<code>webchain-nomination</code> links point to up to {nominations_limit} other
		websites that this node nominates.
	</blockquote>
	<p>
		See the <a href="/doc/manual.md">manual page</a>
		for more information.
	</p>
</details>

<details name="qna">
	<summary>socialize</summary>
	<p>
		If you want to link to this webchain from your site, an old-web style button
		can be created with this form:
	</p>
	<form>
		<label for="button-style">Style</label>
		<br />
		<label class="button-option">
			<input
				type="radio"
				name="button-style"
				value="/button.png"
				bind:group={button}
			/>
			<img
				src="/button.png"
				class="button"
				height="31"
				width="88"
				alt="An old-web style button with the webchain's logo on the right, with some pixel-art chains to the left. This one is more monochrome."
			/>
		</label>
		<label class="button-option">
			<input
				type="radio"
				name="button-style"
				value="/button2.png"
				bind:group={button}
			/>
			<img
				src="/button2.png"
				class="button"
				height="31"
				width="88"
				alt="An old-web style button with the webchain's logo on the right, with some pixel-art chains to the left. This one is tinted more blue."
			/>
		</label>
		{#if browser}
			<br />
			<label for="links-to">Links to</label>
			<select
				name="links-to"
				onchange={(e) => {
					const select = e.currentTarget as HTMLSelectElement
					embed_node = nodes.find((n) => n.at === select.value)
				}}
			>
				<option value="">(none)</option>
				{#each nodes as node (node.at)}
					<option value={node.at}>{node?.label}</option>
				{/each}
			</select>
		{/if}
		<br />
		<label>
			Snippet to include on your site<br /><input
				type="text"
				readonly
				value={snippet}
				onmouseup={(e) => {
					e.currentTarget.select()
				}}
			/>
		</label>
	</form>
	<p>
		The <code>?node</code> query parameter can be used to highlight a specific node
		in the webchain.
	</p>
</details>

<details name="qna">
	<summary>user group</summary>
	<p>
		If you are a member or prospective member, you can come chat in the <a
			href="https://irc.milkmedicine.net"
			rel="external">#webchain channel on irc.milkmedicine.net</a
		>. You may also send an email to
		<a href="mailto:meri@himawari.fun?subject=webchain inquiry"
			>meri@himawari.fun</a
		> if you have a private inquiry.
	</p>
</details>

<details name="qna">
	<summary>feeds & updates</summary>
	<p>
		An RSS feed of webchain members is available at <a href="/rss.xml"
			>rss.xml</a
		>. Crawled member RSS feeds are published as a subscription list in the
		<a href="https://opml.org/" rel="external">OPML</a>
		format at
		<a href="/subscriptions.xml">subscriptions.xml</a>.
	</p>
</details>

<style>
	summary {
		margin: 0;
	}

	details {
		max-width: 40ch;
	}

	details > :nth-child(2) {
		margin-top: 0;
	}

	[name="qna"] {
		padding: 0 0.5rem;
		border: 1px solid transparent;
		margin: -1px 0;
	}

	[name="qna"]:has(> :focus-visible) {
		outline: 2px solid var(--color-primary);
	}

	[name="qna"] summary:focus {
		outline: none;
	}

	[name="qna"]:is(:hover, :focus-visible) {
		border: 1px dashed var(--color-text);
	}

	[name="qna"][open] {
		border: 1px dashed var(--color-text);
		background: var(--color-solid);
	}

	[name="qna"] summary {
		padding: 0.25rem 0;
		font-style: italic;
	}

	[name="qna"] ol li {
		margin: 0.5rem 0;
	}
	pre {
		overflow-x: auto;
	}

	.button {
		image-rendering: pixelated;
		image-rendering: crisp-edges;
		max-width: 100%;
		height: auto;
	}

	form {
		border: double var(--color-border);
		padding: 0.5rem;
	}

	.button-option {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
	}
</style>
