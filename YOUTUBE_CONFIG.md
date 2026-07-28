# Science Made Visual — YouTube Configuration

## Channel
https://www.youtube.com/@ScienceMadeVisual

## Playlists
- Medications (public): https://youtube.com/playlist?list=PLNrMcS-BlJSAmRJvX6ASfMua8TGc0dV-u
- Pharmacy Leadership (public): https://youtube.com/playlist?list=PLNrMcS-BlJSD9ln4zuPqepJMa-X3svrkp

## How to add a new video
When Danny says "new video" or "add latest video":
1. Fetch the relevant playlist URL above to get the latest video IDs and titles.
2. Compare against the `SERIES.medications` or `SERIES.leadership` array in the `<script>` block near the bottom of `index.html`.
3. Add a new `{ id: 'VIDEO_ID', title: 'Episode Title' }` entry to the appropriate array.
4. If it's a new series entirely, add a new array to `SERIES`, a new `<section>` following the pattern of `#medications`/`#leadership`, a container `<div class="series-grid" id="yourSeriesGrid"></div>`, and a `renderSeries('yourSeriesGrid', SERIES.yourSeries)` call.
5. Commit and push to `main` — GitHub Actions redeploys automatically.

## Videos currently on site

### Medications
- `_06TcN-B6sw` — Episode 1: How Do Calcium Channel Blockers Work
- `EvnCz4aHabw` — Episode 2: How Do Statins Work
- `zIMnScXuXqw` — Episode 3: Allergic to Penicillin? Meet the Macrolide Antibiotics
- `jQhUiEYLv5M` — Episode 4: How Do GLP-1 Weight-Loss Jabs Actually Work

### Pharmacy Leadership
- `UFZdjqLfsf4` — Pharmacy & Healthcare Leadership - A new series!
- `_Fe_4-XbOUo` — Clinical leadership: using the expertise around you
- `W9Z2ybj7LxE` — How to retain senior clinicians
