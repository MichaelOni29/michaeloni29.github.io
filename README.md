# Personal academic website — setup guide

A one-page site that lists your publications and refreshes them every Monday from
Google Scholar and ORCID. Hosted free on GitHub Pages. About 30 minutes of setup, once.

## What's in this folder

| File | What it does |
|---|---|
| `index.html` | The website. Your bio, links and CV text are in the `window.SITE` block near the top. |
| `publications.json` | Your publication list, pre-loaded with all 62 papers from your CV and Web of Science CV (Oct 2026). The weekly sync adds new papers and updates citations; it never removes entries. |
| `scripts/update_publications.py` | Pulls your publications from Google Scholar and ORCID/OpenAlex and merges them into `publications.json`. |
| `.github/workflows/update-publications.yml` | Runs the script every Monday and commits the result. |

## Step 1 — Your IDs (already done)

Your five profile IDs are already in the `ids:` section of `index.html`:

| Profile | ID |
|---|---|
| Google Scholar | `7PQsNQ4AAAAJ` |
| Scopus | `57191926774` |
| ORCID | `0000-0002-0272-4825` |
| Web of Science | `X-7347-2019` |
| ResearchGate | `Michael-Oni` |

To remove a paper or fix a title, edit `publications.json` directly; to add one by hand, copy an existing entry.

## Step 2 — Put the site on GitHub Pages (10 min)

1. Create a free account at github.com.
2. Create a new **public** repository named `<your-username>.github.io`
   (this gives you the address `https://<your-username>.github.io`).
3. Upload everything in this folder, **including the hidden `.github` folder**
   (drag the whole folder into "Add file → Upload files"; if `.github` doesn't upload,
   create the file `.github/workflows/update-publications.yml` by hand and paste its contents).
4. Repository **Settings → Pages** → Source: *Deploy from a branch* → `main` / root → Save.

Your site is live within a couple of minutes.

## Step 3 — Turn on automatic updates (5 min)

Repository **Settings → Secrets and variables → Actions**:

- **Variables** tab → add `SCHOLAR_ID` = `7PQsNQ4AAAAJ`, `ORCID_ID` = `0000-0002-0272-4825`, and `CONTACT_EMAIL` = `mooni@abu.edu.ng`.
- **Secrets** tab → add `SERPAPI_KEY` (optional but recommended, see below).

Then go to the **Actions** tab → *Update publications* → **Run workflow** to fill the list now.
After that it runs by itself every Monday.

### Why the SerpAPI key is recommended

Google Scholar has no official API and often blocks automated requests from cloud servers.
The script tries three routes and merges whatever succeeds:

1. **SerpAPI** (serpapi.com) — a paid service with a free tier that easily covers one sync a week. Most reliable way to read Scholar.
2. **scholarly** — free, scrapes Scholar directly. Works some weeks, gets blocked on others.
3. **OpenAlex via your ORCID** — free and reliable. Adds DOIs and full author lists.

Even with no SerpAPI key, keeping your **ORCID** complete means the site always has an accurate list.
If every route fails in a given week, the old list stays up — the page never goes blank.

## Step 4 — Make it yours

- Edit the CV, achievements and research sections directly in `index.html` (plain HTML).
- A custom domain (e.g. `michaeloni.com`, roughly $10–15/year) can be pointed at GitHub Pages in Settings → Pages.

## Keep your sources clean

The site is only as good as your profiles:

- In Google Scholar, merge duplicate entries and remove papers that aren't yours.
- In ORCID, connect Crossref and Scopus under *Works → Add → Search & link* so new papers arrive automatically.
- Link ORCID to Scopus and Web of Science so all four profiles stay in agreement.
