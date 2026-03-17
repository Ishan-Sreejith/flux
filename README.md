# Flux

Flux is a local natural language system with a fast web grounded answer engine and an optional experimental mode. It has two parts:

1. Local backend and UI for full features.
2. A static GitHub Pages site that runs entirely in the browser.

## Local version

- Backend: `flux_app`  
- UI: `flux_app/frontend`

Start the local stack:

```
bash /Users/ishan/flux/flux_app/start.sh
```

Open the UI in your browser and use the Experimental toggle to blend in:

- Symbolic traits from the animal taxonomy
- Lightweight web search from the experimental stack
- A tiny experimental answer brain

## GitHub Pages version

The static site lives in `docs`. It includes:

- A small in-browser model
- A terminal mode
- A quick evaluation panel
- Optional Wikipedia lookup

To publish, set GitHub Pages to the `/docs` folder on the main branch.
