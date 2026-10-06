# Websites: personal page + Utah Digital Twin Lab

One repo builds two responsive static sites that share a design system:

| Site | Output | Deploys to |
|---|---|---|
| Personal | `dist/personal/` | users.cs.utah.edu/~shankar (rsync to `public_html`) |
| Lab (UDTL) | `dist/lab/` | varunshankar.com (GitHub Pages; domain at Squarespace) |

## Build and preview

```bash
pip install jinja2 pyyaml
python build.py --serve     # http://localhost:8000/personal/  and  /lab/
```

## Updating content (edit YAML; no HTML needed)

| What | File |
|---|---|
| Papers (title, authors, venue, year, tags, arXiv/DOI/url, optional `code`) | `shared/data/publications.yaml` |
| Grants (`status: active` shows on Funding page; `show_amounts` toggle) | `shared/data/grants.yaml` |
| People, alumni, collaborators (add `photo:` for headshots) | `shared/data/people.yaml` |
| Research thrusts (KaTeX math allowed) | `shared/data/research.yaml` |
| News, talks, teaching, appointments, service | `shared/data/cv.yaml` |
| Nav, email, recruiting on/off | `personal/site.yaml`, `lab/site.yaml` |
| Headshot | `personal/static/images/varun.jpg` and `lab/static/images/varun.jpg` |
| CV PDF | `personal/static/VarunShankar-cv.pdf` |

The lab's "student" underlining in author lists comes from `group_members` at the top of `publications.yaml`.

## Deploy: personal site

Connect GlobalProtect first, then from this folder:

```powershell
.\deploy_personal.ps1        # Windows (PowerShell, built-in OpenSSH)
```
```bash
./deploy_personal.sh          # macOS / Linux / WSL
```
Both log in as `shankar@shell.cs.utah.edu`, back up the current `public_html` on the server (`public_html_backup_<date>`), then copy `dist/personal/` into `public_html/`. The zip already contains a built `dist/`, so Python is only needed if you change content.

## Deploy: lab site → varunshankar.com

1. Push this repo to GitHub. In the repo, go to Settings → Pages and set Source to "GitHub Actions". The included workflow (`.github/workflows/lab.yml`) builds and publishes the site on every push to `main`.
2. In Settings → Pages → Custom domain, enter `varunshankar.com` and tick "Enforce HTTPS" once it becomes available.
3. In Squarespace, go to Domains → varunshankar.com → DNS. Remove the Squarespace default records, then add:
   - `A  @  185.199.108.153`
   - `A  @  185.199.109.153`
   - `A  @  185.199.110.153`
   - `A  @  185.199.111.153`
   - `CNAME  www  <github-username>.github.io`
4. If the domain is also attached to a Squarespace *website*, that site stops serving once DNS points to GitHub. You can then cancel the site plan and keep the domain registration.
