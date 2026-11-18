# WealthFlow — Mobile Finance Manager (iPhone Safari PWA)

100% mobile-first edition of WealthFlow, completely isolated from the desktop app while sharing the exact same **Turso database** and **batched service layer** (`database.py` & `services/*`).

## Preview the Figma Design Board
Open `design/figma_board.html` in any browser to inspect all 6 iPhone (`393 × 852`) artboards interactively, or import `design/design-tokens.json` into Figma Tokens Studio.

## Run Locally (Separate Port)
From the `Finance Manager` root folder:
```bash
streamlit run "Mobile Finance Manager/mobile_app.py" --server.port 8502
```
Open `http://localhost:8502` (or DevTools Device Mode → iPhone 15 Pro `393 × 852`).

## Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) → **Create app** → **Deploy a public/private app from GitHub**.
2. Select repository **`Ganeshnarapareddy/WealthFlow`**, branch **`main`**.
3. Set **Main file path** to:
   ```text
   Mobile Finance Manager/mobile_app.py
   ```
4. Under **Advanced settings → Secrets**, paste the exact same `TURSO_URL`, `TURSO_TOKEN`, and `COOKIE_PASSWORD` used by the desktop app.
5. Click **Deploy**.

## Add to iPhone Home Screen (Safari PWA)
1. Open your deployed mobile Streamlit Cloud URL in **Safari** on iPhone.
2. Tap the **Share** button (square with up arrow) → **Add to Home Screen** → **Add**.
3. Launch **WealthFlow** directly from your Home Screen — your login stays persisted via `localStorage` + encrypted cookies, safe areas (Dynamic Island & Home Bar) are respected automatically, and inputs never auto-zoom.
