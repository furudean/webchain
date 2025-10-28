---
title: "webchain Manual"
---

# webchain Manual

This document describes some common patterns for users interested in the
milkmedicine webchain.

## Joining the webchain

To join this webchain, you must be nominated by an existing member of the graph.
You can request a nomination by contacting any existing member of the webchain
and asking them to add a link to your website.

Once your page is nominated, you can add others to the webchain via your own
nominations.

## Nominating sites

To nominate a site, you add markup to your webpage. A full example is shown below:

```html
<!DOCTYPE html>
<html lang="en">
	<head>
		<meta charset="UTF-8" />

		<link rel="webchain" href="https://webchain.milkmedicine.net" />
		<link rel="webchain-nomination" href="https://foo.example" />
		<link rel="webchain-nomination" href="https://bar.example" />

		<title>Example Webchain Document</title>
		<meta
			name="description"
			content="Example webchain document with two nominations"
		/>
		<meta name="theme-color" content="#ff6600" />
	</head>
	<body>
		Example webchain document with two nominations
	</body>
</html>
```

In this example, the webpage at this URL is nominating two other websites,
`https://foo.example` and `https://bar.example`, to join the webchain.

The relevant link relations are as follows:

| `rel`                        | description                                       |
| ---------------------------- | ------------------------------------------------- |
| `webchain`                   | URL of the webchain seed document                 |
| `webchain-nomination`        | URL of a nominated website                        |
| `webchain-nominations-limit` | Maximum number of nominations allowed (seed only) |

Your `<link>` tags don't need to be placed in the `<head>` section, as the
scraper is quite forgiving.

## Crawler

The crawler discovers the webchain by starting from a seed. It follows
nominations until all paths are exhausted.

If a page cannot be reached, or does not contain valid webchain markup, it is
ignored. The exact heuristics are described in the [specification](spec.md).

### Metadata

The crawler also collects metadata about each page, including the title and
description. This is extracted from the standard HTML `<title>` tag and
`<meta name="description">` tag, if present. We also look at
[Open Graph metadata](https://ogp.me/) and
[Twitter Cards](https://developer.x.com/en/docs/x-for-websites/cards/overview/abouts-cards).

If you define a
[`<meta name="theme-color">`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meta/name/theme-color)
tag, this color will be associated with your page in the visualizer.

### Favicons

The crawler attempts to fetch the favicon for each page in the webchain. It
first looks for a `<link rel="icon" href="...">` tag in the HTML document. If
not found, it falls back to `/favicon.ico` at the root of the domain. This
generally follows the same logic as web browsers.

### My page is not being crawled!

If your page is not being crawled, please verify that:

- You can visit the page yourself in a web browser
- Your page contains valid webchain markup as described above
- An existing member of the webchain has nominated your page

Your page must also be reachable by the crawler. Some common issues and
solutions are described in the table below:

| Problem                                      | Solution                                                        |
| -------------------------------------------- | --------------------------------------------------------------- |
| You are using `robots.txt` to block crawlers | Allow the user-agent `WebchainSpider` in your `robots.txt` file |
| Your server is blocking certain IP-ranges    | Add an exception for the crawler's IP address: `134.199.140.52` |

If you continue to have issues, please contact the maintainer of the webchain.
