# Flux Lite Web Demo (GitHub Pages)

This folder is a static site. To deploy on GitHub Pages:

1. Push this repo to GitHub.
2. In GitHub → Settings → Pages:
   - Source: `Deploy from a branch`
   - Branch: `main` (or `master`) and `/docs` folder
3. Save. GitHub Pages will serve the site.

Local dev:

```bash
bash /Users/ishan/flux/docs/serve.sh
```

The `.nojekyll` file prevents GitHub Pages from ignoring the `data/` folder.
