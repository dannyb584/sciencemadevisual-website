# Deploying Science Made Visual to www.sciencemadevisual.co.uk

## Step 1 — Push to GitHub
A new **public** repository called `sciencemadevisual-website` should exist at
https://github.com/dannyb584/sciencemadevisual-website before pushing.

```bash
cd "path/to/sciencemadevisual-website"
git init
git add .
git commit -m "Initial website"
git branch -M main
git remote add origin https://github.com/dannyb584/sciencemadevisual-website.git
git push -u origin main
```

---

## Step 2 — Enable GitHub Pages
1. Go to the repository on GitHub
2. Click **Settings** → **Pages** (left sidebar)
3. Under **Build and deployment → Source**, choose **Deploy from a branch**
4. Branch: **main**, folder: **/ (root)** → Save
5. It will be live at `https://dannyb584.github.io/sciencemadevisual-website/` within a minute or two

---

## Step 3 — Point the IONOS domain at GitHub Pages
Log into IONOS and add these DNS records for `sciencemadevisual.co.uk`:

| Type  | Host | Value                          |
|-------|------|--------------------------------|
| A     | @    | 185.199.108.153                |
| A     | @    | 185.199.109.153                |
| A     | @    | 185.199.110.153                |
| A     | @    | 185.199.111.153                |
| CNAME | www  | dannyb584.github.io            |

DNS changes can take up to 24 hours to propagate. GitHub Pages will automatically provision an SSL certificate (HTTPS) once DNS is live.

---

## Step 4 — Set the custom domain + enable HTTPS in GitHub Pages
1. Go to **Settings → Pages**
2. Under **Custom domain**, enter `www.sciencemadevisual.co.uk` and save (this writes the `CNAME` file already committed in this repo)
3. Once DNS propagates, tick **Enforce HTTPS** ✓

---

## Updating the site later
Every push to `main` redeploys automatically within a minute or two via GitHub Pages.

```bash
git add .
git commit -m "Update content"
git push
```
