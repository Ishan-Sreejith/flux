# Animal1010101 Web Demo (GitHub Pages)

This folder is a static site. To deploy on GitHub Pages:

1. Push this repo to GitHub.
2. In GitHub → Settings → Pages:
   - Source: `Deploy from a branch`
   - Branch: `main` (or `master`) and `/animal1010101_web` folder
3. Save. GitHub Pages will serve the site.

Local dev:

```bash
bash /Users/ishan/flux/animal1010101_web/serve.sh
```

The `.nojekyll` file prevents GitHub Pages from ignoring the `data/` folder.
