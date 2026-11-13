# Min&Su Library

A private, chaptered library for Min and Su. Each chapter is its own page, with a gallery, trips, dates, notes, and achievements. Both of you can add to it over time. Anyone with the link can read. Choosing "I'm Min" or "I'm Su" is only needed when you add or edit, so a note remembers who wrote it.

## Local setup

Use Python 3.12. The project pins that version in `.python-version` for Vercel. Python 3.13 can run it locally if 3.12 is not installed yet.

```bash
cd path/to/Min-Su-Library
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

- `DATABASE_URL` — the TigerData connection string, including `?sslmode=require`
- `SECRET_KEY` — a long random string that signs the who-cookie and the edit cookie. Generate one with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

- `EDIT_PASSCODE` — optional. Leave it empty and writes are open. Set a shared phrase if you want every add, edit, and delete to ask for it once on each browser.

Then create the tables and the sample chapters:

```bash
python scripts/init_db.py
uvicorn app:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The home page is readable immediately. The first time you add something, pick **I'm Min** or **I'm Su**. That choice is stored in a signed cookie for a year. Use the small **switch** link in the header to change it. A note can only be edited or deleted by the person who wrote it. Everything else can be changed by either of you.

`.env` is gitignored. Do not commit it.

Run `init_db.py` once. Running it again will not delete chapters you added. It also will not overwrite a sample row you edited. If you delete a sample row, a later run can put that sample id back. It applies `db/migrations/` as well, so an older database that still has emails and password hashes is brought in line (those columns are dropped, and `slug` plus `accent_color` are added).

## Create the TigerData database

1. Sign in at [Tiger Console](https://console.cloud.tigerdata.com/).
2. Click **New service**. Shared compute is the free option. This app is ordinary Postgres, so **Create with plain PostgreSQL** is enough. A Timescale service works too.
3. Choose **Development**, name the service (for example `min-su-library`), and create it.
4. Download the config file when it is offered. That download is the only time the password is shown. If you lose it, reset the service password in the console.
5. Copy the connection string. It looks like:

```text
postgresql://tsdbadmin:PASSWORD@HOST.tsdb.cloud.timescale.com:PORT/tsdb?sslmode=require
```

6. Paste it into `.env` as `DATABASE_URL`. If a character in the password is `@`, `:`, `/`, or `#`, it must be URL-encoded. The string from the console usually already is.
7. From your laptop, with the venv active, run `python scripts/init_db.py`.

Do this once, against the real database, before or right after the first deploy. Do not run it from the Vercel build. A deploy should not reload sample data.

You can also open the SQL editor in Tiger Console and connect from there. The app itself uses `psycopg` with short-lived connections, which is what you want on Vercel.

## Deploy to Vercel

Vercel detects FastAPI with no `vercel.json`. It loads `app` from `app.py`. Files in `public/` are served from the CDN (`public/css/base.css` is `/css/base.css`). `.python-version` pins Python 3.12.

1. Push this project to a **private** GitHub repository.
2. In Vercel, choose **Add New → Project** and import that repository.
3. Leave the build command and output directory empty. The framework should come up as FastAPI.
4. Add the environment variables:
   - `DATABASE_URL` — the same TigerData string
   - `SECRET_KEY` — a long random string. It can differ from the one on your laptop. Changing it signs everyone out of the who-cookie.
   - `EDIT_PASSCODE` — optional. Set the same phrase you use locally if you want writes protected. Leave it unset to leave writes open.
5. Deploy.
6. If you have not already, run `python scripts/init_db.py` on your laptop so the tables exist.
7. Open the deployment URL. Reading needs no sign-in.

The who-cookie and the edit cookie are marked Secure on Vercel because the site is served over HTTPS.

## How your partner contributes

Add them on GitHub: repository **Settings → Collaborators → Add people**, with the **Write** role. Keep the repository private.

They then:

```bash
git clone git@github.com:YOUR_ACCOUNT/YOUR_REPO.git
cd YOUR_REPO
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Send them `DATABASE_URL`, `SECRET_KEY`, and `EDIT_PASSCODE` (if you set one) through a password manager. Not through git.

They do **not** need to run `init_db.py` if you already did. Then:

```bash
uvicorn app:app --reload
```

On the site they pick **I'm Min** or **I'm Su**. That is the whole "account". If a passcode is set, the first edit on that browser asks for it and then remembers it for a year. Day to day in git: `git pull` before starting, make the change, commit, and push. If you are both working at the same time, use a branch and open a pull request so you do not overwrite each other.

Either person can create, edit, and delete chapters and section entries. A note is the exception: only the person who wrote it can edit or delete it.

## How to add a chapter

No code change. Go home, open **Add a chapter**, and save. If you have not chosen a name yet, the site asks you to first. The new chapter shows up as a card and gets a page at `/chapter/NUMBER`.

On that page, each section has its own add form:

- **Gallery** — image path or URL, caption, date
- **Trips** — title, location, dates, description, cover
- **Dates** — title, place, date, description, optional rating, photo
- **Notes** — the letter, and the date. It is signed with whoever you picked, Min or Su.
- **Achievements** — title, date, personal or shared, description, photo

To use a photo you already have, put the file in `public/assets/`, commit it if you want Vercel to serve it, and type `assets/your-file.jpg` in the form. A full `https://` URL also works. The database stores that path or URL, never the image bytes.

File upload is not built yet. The swap point is `save_image()` in `storage.py` (`# TODO: replace with Vercel Blob upload`). Forms should keep calling that function.

The logo files under `public/assets/brand/` are generated from `logo.png`:

```bash
python scripts/make_brand_assets.py
```

The home page can draw a crystal ball behind that logo. `SHOW_CRYSTAL_BALL` in `config.py` turns it on. When it is false, the still logo is used and the ball's CSS and scripts are not loaded. The WebGL library is already bundled, so a Vercel build does not need Node. To rebuild that bundle after changing the `ogl` version:

```bash
npm install ogl@1.0.11
npx esbuild node_modules/ogl/src/index.js --bundle --format=esm --outfile=public/js/vendor/ogl.js
```

## Optional edit passcode

Leave `EDIT_PASSCODE` empty and writes stay open. Set it when you want a shared phrase in front of adding, editing, or deleting. Viewing is never blocked. A correct phrase sets a signed cookie for a year. A wrong one waits a moment, and this server process stops trying after 5 misses in 10 minutes. On Vercel that count is per running instance, so it is a light brake, not a lock.

There are no user passwords. The two rows in `users` are Min (`min`) and Su (`su`).

## Where the next pass plugs in

- Colors, type, and spacing: the `:root` block in `public/css/base.css`.
- The idle logo float is CSS, and only when the crystal ball is off. It is turned off when someone prefers reduced motion.
- Other motion: elements already have `data-animate` (for example `data-animate="fade-up"`). Add the behavior in `public/js/animations.js`. The CSS already short-circuits animation for reduced motion.
- Uploads: `storage.py`.

## Layout

```text
app.py                  FastAPI app (the Vercel entry)
config.py               site name
routes/                 pages, who-you-are, and the section forms
db/                     connection, schema.sql, seed.sql, migrations, queries
templates/              pages and one partial per section
public/css              tokens in base.css, pieces in components.css
public/js               lightbox, page behavior, and the vendored crystal ball
public/assets           your images, the logo, and placeholder plates
scripts/init_db.py      creates tables, applies migrations, loads the seed
scripts/make_brand_assets.py
storage.py              the image-path function uploads will replace
```

Pages: `/` and `/chapter/{number}` are open to read. `POST /who` stores the chosen person. `POST /passcode` stores the edit passcode when one is set. Forms use a double-submit CSRF cookie, not a login session.
