# Flux Evolver IDE

Hyper-modern evolutionary algorithm IDE for the browser. This project implements a web-based simulation UI for the "Formula Maker" system.

## Version
Current Version: **v0.1.0**

## Features
- **Smooth Animations**: High-refresh-feel UI with liquid borders and 60fps chart rendering.
- **Human-Readable Algorithms**: Transform complex parametric mappings into readable logic steps.
- **Interactive Guide**: Integrated onboarding for first-time users.
- **Theme Engine**: Support for Cyber Synth, Matrix, Solar Flare, and Arctic Frost themes.
- **Deterministic Tracking**: Version bumping and change logging integrated into the UI.

## Deployment
This folder is designed for GitHub Pages.

1. Push the repo to GitHub.
2. In GitHub Settings, open Pages.
3. Choose Deploy from a branch.
4. Select the `main` branch and the `/docs` folder.

## Local Development
Run the development server:
```bash
./docs/serve.sh
```

The `.nojekyll` file ensures that the `data/` folder is accessible in the deployed environment.

## Runtime Notes
- The app loads preset datasets from relative `data/*.json` paths, which works for both root domains and project pages.
- No build step is required; this is a static HTML/CSS/JS site.
