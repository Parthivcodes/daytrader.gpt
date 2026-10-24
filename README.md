# Free-only cloud deployment

No paid cloud service has been created. The paid Render Blueprint was removed.
Deploy only on an Oracle Always Free-eligible VM with available quota in the
account's home region. Never upgrade the account or select paid add-ons.

Suggested VM: Always Free VM.Standard.E2.1.Micro (1 GB RAM), eligible Ubuntu
image and a 50 GB boot disk. Alternative: eligible A1.Flex, 1 OCPU / 1 GB RAM.
Verify the Always Free labels and existing account quotas before provisioning.
Use included public connectivity; no paid NAT gateway, load balancer or image.
Restrict inbound SSH to the operator's IP. No public HTTP service is needed.

Free capacity may be unavailable and Oracle can reclaim low-utilization VMs.
This is not a guarantee of uninterrupted trading or timely exits. Do not
generate artificial load to defeat the provider's idle-reclamation rules.

The bot keeps the PAPER-only $5,000 capital ceiling and $100 planned-risk
ceiling. Automatic trades use at most $3,750 and $90 planned risk, one trade
attempt per session, broker-held stop/target orders, and a timed exit beginning
before 01:25 IST next day (earlier for short exchange sessions). Stop slippage
can exceed planned risk. This strategy is not backtested or proven profitable.

## VM installation

Use Ubuntu 24.04 / Python 3.12. Clone this repository to /opt/daytrader.gpt,
install python3-venv, create /opt/daytrader.gpt/.venv and install requirements.txt
into it. Run the test suite before starting the service. Create an unprivileged
system user and group named alpaca-paper.

Create /etc/alpaca-paper.env, owned by root with mode 0600. Add only the PAPER
credentials there, never in Git or chat:

```text
ALPACA_API_KEY=<paper key>
ALPACA_SECRET_KEY=<paper secret>
ALPACA_PAPER_TRADE=true
PAPER_ENTRIES_ENABLED=false
```

Copy deploy/alpaca-paper.service to /etc/systemd/system/. Run
`sudo systemctl daemon-reload` and `sudo systemctl enable --now alpaca-paper`.
New entries remain paused initially. Systemd restarts the worker after failure
and at boot. State persists on the boot disk at /var/lib/alpaca-paper.

## Cutover

1. Verify fresh logs with `sudo journalctl -u alpaca-paper -n 30` and read-only
   Alpaca connectivity. Ensure no account positions or orders are open.
2. Pause entries on the laptop, disable and stop Windows task
   AlpacaPaperStandalone, and verify its process has exited.
3. Recheck the broker is flat. If anything remains, reconcile before cutover.
4. Change PAPER_ENTRIES_ENABLED to true in the environment file, restart the
   cloud service, and verify its new heartbeat. Never run both hosts at once.

To pause new entries, set the switch false and restart, or create the file
/var/lib/alpaca-paper/PAUSE_ENTRIES. Existing exits continue. Do not stop the
service with an open trade; timed exits require both the runner and Alpaca.
The broker-held stops and targets do not require Codex or the cloud process.

Durable intents, stable order IDs and broker history protect against duplicate
orders and resetting the daily allowance. Linux flock excludes concurrent
processes on this disk, not independent hosts. Never delete or restore older
state files without first reconciling actual broker activity.

The cloud service is **not deployed yet**. Account access, free capacity,
installation, verification and the laptop-to-cloud cutover remain required.

Sources checked October 24, 2026:
- [Oracle Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
- [Oracle free account rules](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm)
- [Render free limitations](https://render.com/docs/free)
