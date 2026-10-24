# Alpaca paper day trader

Single-instance, always-on Python background worker. No Codex session, OpenAI
API, laptop, or browser is required after cloud deployment.

**Limits:** paper-only API, $5,000 capital ceiling, $100 maximum planned risk per
trade. The automatic strategy currently uses at most $3,750 and $90 planned
risk, one attempted trade per session, long whole shares only. Stop slippage
can exceed planned risk. This is experimental paper trading, not a proven or
backtested profitable strategy.

Scans AAPL, MSFT, NVDA, AMZN, GOOGL, META and SPY using IEX. Uses a 15-minute
opening-range breakout confirmed by a completed five-minute bar, volume and
VWAP; fresh quote/spread checks; broker-held bracket stop and 2R take profit.
Cancels unfilled entries after three minutes. Starts timed exits one minute
before the earlier of 01:25 IST next day or five minutes before exchange close.

## Render deployment

`render.yaml` defines one background worker (0.5 CPU / 512 MB), with a 1 GB
persistent disk. Estimated base hosting cost $7.25/month, before taxes, workspace
charges and usage extras; verify in the Render creation screen.

Create a Blueprint from this repository in the intended Render workspace.
Configure `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` as secrets with PAPER account
credentials. Do not put credentials into source files, commits, chat, or logs.
Set **`PAPER_ENTRIES_ENABLED=false` for initial deployment**. Cloud startup
refuses to run without a persistent mount, paper credentials, and an explicit
entries switch. Review the deploy logs before enabling entries.

Source files remain separate from `/var/data/trader`, where the worker keeps
its active plan, session reservations, submission intents, lock, and logs.
Restarting or deploying never overwrites existing trading state. Linux flock
prevents a second process from using the same state directory. Render disks
also restrict the service to a single instance. Do not create a second service
with the same paper credentials; separate hosts do not share an OS lock.

## Cutover from Windows

1. Deploy the cloud worker with `PAPER_ENTRIES_ENABLED=false` and confirm a fresh
   healthy log heartbeat and successful read-only `--check` against Alpaca.
2. Check that the account has no open positions or orders. If it does, do not
   cut over; let the existing runner finish and verify flat first.
3. Pause local entries, disable and stop Windows task `AlpacaPaperStandalone`,
   and verify its process has exited. Leave the local pause marker in place.
4. Recheck broker positions and orders after the local process stops.
5. Change `PAPER_ENTRIES_ENABLED=true` on Render and deploy. Confirm its new
   heartbeat. Do not re-enable the local task while the cloud bot is active.

The worker also checks today's broker order history before a new selection,
so migrating an already completed daily trade does not reset its allowance.
If unexplained positions/orders exist without a saved plan, it reports an
attention state and refuses new entries. Do not delete or restore an older
state disk without reconciling all broker activity first.

## Operations

- Read status from Render logs (state changes immediately; routine heartbeat
  every five minutes). Local state is at `/var/data/trader/status.json`.
- Read-only connection check: `python trader/standalone/runner.py --check`.
- To pause new entries set `PAPER_ENTRIES_ENABLED=false` and deploy, or create
  `/var/data/trader/PAUSE_ENTRIES` in the service shell. Existing exits continue.
- Never suspend the worker or remove its disk with an open trade. Timed exits
  depend on the worker and Alpaca availability; stop/target legs stay at Alpaca.
- Automatic deploys are disabled. Prefer changes outside trading hours while
  flat: a disk-backed deploy briefly interrupts the worker.
- A SIGTERM stops after the current reconciliation cycle; durable intents and
  broker client IDs prevent blind order resubmission on restart.
- Broker credentials are read from environment variables in cloud mode. The
  Windows-only config fallback is disabled for cloud deployments.

Run offline tests with `python -m unittest discover -s tests -p test_standalone.py -v`.
