# Montgomery County Rental Dashboard — Setup Guide

No coding experience needed. Follow these steps in order.
Total setup time: about 15 minutes.

---

## What you'll need
- A free **GitHub account** — this hosts your website AND your data
- That's it. No Google account, no other services.

---

## What's in this folder

| File | What it does |
|---|---|
| `index.html` | Your dashboard website |
| `data.json` | The rental data (starts with sample data, auto-updates quarterly) |
| `update_data.py` | Script that fetches fresh data from Zillow every quarter |
| `.github/workflows/update-data.yml` | The scheduler that runs the script automatically |

---

## Step 1 — Create a free GitHub account

1. Go to **github.com/signup**
2. Choose a username, enter your email, create a password
3. Verify your email address

---

## Step 2 — Create a new repository

A "repository" is just a folder on GitHub that holds your website files.

1. Once logged in, click the **+** icon in the top-right corner
2. Click **New repository**
3. Name it: `mc-rental-dashboard`
4. Set visibility to **Public** (required for the free website hosting)
5. Leave everything else as-is and click **Create repository**

---

## Step 3 — Upload your files

1. On your new repository page, click **uploading an existing file**
2. Open the folder you downloaded and drag ALL files into the upload area:
   - `index.html`
   - `data.json`
   - `update_data.py`
3. Click **Commit changes** (green button at the bottom)

> **The workflow file needs special handling.**
> The `.github/workflows/update-data.yml` file lives inside folders.
> GitHub's uploader can create folders for you — when you drag it in,
> it will show the full path `.github/workflows/update-data.yml` and that's correct.
> If it doesn't appear, create it manually:
> - Click **Add file → Create new file**
> - In the filename box type: `.github/workflows/update-data.yml`
> - Copy and paste the contents of that file
> - Click **Commit new file**

---

## Step 4 — Turn on GitHub Pages (your website)

1. In your repository, click **Settings** (top menu bar)
2. In the left sidebar, scroll down and click **Pages**
3. Under "Source", click the dropdown and select **Deploy from a branch**
4. Under "Branch", select **main** and keep **/ (root)**
5. Click **Save**
6. Wait about 60 seconds, then refresh the page
7. A green box will appear with your website address:
   `https://YOUR-USERNAME.github.io/mc-rental-dashboard`

**Bookmark that link and share it with your peers.**
It never changes.

---

## Step 5 — Run the first data update

The dashboard already works with sample data, but let's pull in real Zillow data now.

1. In your repository, click the **Actions** tab
2. You'll see **Quarterly Rental Data Update** in the left list — click it
3. Click the **Run workflow** dropdown on the right
4. Click the green **Run workflow** button
5. A yellow circle will appear — this means it's running (takes about 1 minute)
6. When it turns into a green checkmark, the update is done
7. Reload your website — it now shows real Zillow data for Montgomery County

---

## How auto-updates work

Every **January 1st, April 1st, July 1st, and October 1st** GitHub automatically:
1. Runs `update_data.py` — fetches the latest Zillow rent data
2. Saves it to `data.json` in your repository
3. Your website reads `data.json` on every page load — so it's always current

**You don't need to do anything.** Just open the website and the numbers will be up to date.

---

## How to update data manually (optional)

If you want to change a number between quarterly updates:

1. Go to your GitHub repository
2. Click on `data.json`
3. Click the **pencil icon** (Edit this file) in the top right
4. Change any numbers you like — the format is straightforward
5. Click **Commit changes**
6. Your website updates within seconds

---

## Sharing with peers

Just send them your URL:
`https://YOUR-USERNAME.github.io/mc-rental-dashboard`

The page works on phones, tablets, and computers.
No login required to view it.
It can be bookmarked like any other website.

---

## Troubleshooting

**"Could not load data" on the website**
→ Make sure `data.json` was uploaded to the repository (Step 3).

**The Actions tab shows a red X**
→ Click on it to see the error message. The most common fix is re-running it —
   sometimes Zillow's servers time out. Click "Re-run jobs" and try again.

**The website URL gives a 404 error**
→ GitHub Pages can take up to 5 minutes to activate after Step 4. Wait and refresh.

**I want to add a neighborhood that's missing**
→ Edit `data.json` manually (see "How to update data manually" above) and add a new entry
   following the same format as the existing ones.
