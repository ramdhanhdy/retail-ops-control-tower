# Dashboard screenshot note

A PNG screenshot was not captured in this run because the browser automation environment could not launch Chrome. The dashboard server was started locally with Streamlit and verified by source, helper, and HTTP checks.

To capture manually after installing browser tooling, run:

```bash
. .venv/bin/activate
streamlit run dashboard/app.py --server.headless true
```

Then open http://127.0.0.1:8501 and save the home view as docs/screenshots/dashboard-home.png.
