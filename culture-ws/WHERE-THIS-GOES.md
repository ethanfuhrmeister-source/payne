# This belongs in its own repo

This folder is a complete, standalone static site for **Culture** (Liberty Plaza,
9th floor, Winston-Salem) — an unrelated project to the site at the root of this
repository. It is parked here only because the session that built it could not
create a new GitHub repository (the integration lacks the `create repo`
permission), and the work would otherwise have been lost.

## Moving it to its own repo

Create an empty repo on GitHub named `culture-ws`, then:

```bash
git clone https://github.com/ethanfuhrmeister-source/payne.git /tmp/payne
cd /tmp/payne
git checkout claude/website-design-deck-eem34y

mkdir ~/culture-ws && cp -r culture-ws/. ~/culture-ws/
rm ~/culture-ws/WHERE-THIS-GOES.md

cd ~/culture-ws
git init -b main
git add -A
git commit -m "Build the Culture WS site from the design deck"
git remote add origin https://github.com/ethanfuhrmeister-source/culture-ws.git
git push -u origin main
```

Then delete the `culture-ws/` folder from this branch so the two projects stop
sharing a repository.

## Publishing it

Settings → Pages → Deploy from a branch → `main` → `/ (root)`.
Then update the two `https://culturews.com` URLs in `sitemap.xml` and `robots.txt`.

See `README.md` in this folder for the full rundown.
