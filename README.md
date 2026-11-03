# nq-data

Daily 1-minute and 5-minute bars for NQ (E-mini Nasdaq-100, front month,
Yahoo symbol `NQ=F`), one CSV per CME trading session.

- `data/1m/NQ_YYYY-MM-DD_1m.csv` — overnight + RTH + post-close of that session
- `data/5m/NQ_YYYY-MM-DD_5m.csv` — same, 5-minute bars
- `data/INDEX.md` — list of all files currently in the repo

Columns: `time_et, open, high, low, close, volume` — times are New York time,
bar open time. A session runs 18:00 ET (previous evening) to 17:00 ET; RTH is
09:30–16:00 ET.

The workflow in `.github/workflows/fetch.yml` runs Mon–Fri at 23:30 UTC and
commits new files. Run it manually from the **Actions** tab the first time.

Data source is Yahoo Finance (free, delayed, occasionally a missing minute).
Volume on futures from Yahoo is unreliable — use it for shape, not for exact
numbers. Yahoo only keeps 1m history for ~7 days, so if the workflow is
disabled for more than a week those days are lost.
