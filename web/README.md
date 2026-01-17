# web app

visualizer web page to inspect the current state of a webchain.

## developing

once you've created a project and installed dependencies with `npm install` , start a development server:

```sh
npm run dev
```

you will need to place an active webchain (with metadata) in `static/crawler/current.json`. You generate it using [the crawler](../crawler/). in production this file would be updated on a cadance to represent an up-to-date state. you can shadow the `/crawler/current.json` path using a reverse proxy like nginx.

you also need to place a file called `/crawler/heartbeat.json`, which contains the keys `start` and `end`, which represent when the last crawl was done (may not be the same as a cached static crawl). for example:

```json
{
	"start": "2026-01-17T01:30:01.833046+00:00",
	"end": "2026-01-17T01:32:04.149410+00:00"
}
```

## building

to create a production version of your app:

```sh
npm run build
```

the app builds to a node environment, but this is customizable. you can preview the production build with `npm run preview`.
