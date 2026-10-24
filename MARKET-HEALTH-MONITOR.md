# Free market-hours monitoring

The public repository's Daytrader market-hours health check workflow requests
the deployed /healthz endpoint every five minutes, weekdays 12:03-21:58 UTC
(17:33-03:28 IST). This window covers US daylight and standard trading hours.
On Monday October 26, 2026, monitoring begins at 17:33 IST, before the 19:00 IST
market opening. Each request can wake an idle Render Free service.

It uses only standard ubuntu-latest runners in a public repository. No Alpaca
trading credentials or paid resources are used. User-approved encrypted
Actions secrets provide the email API key, recipient and read-only dashboard
access code. Repository contents permission is read-only. If repository
visibility changes to private, the workflow job is skipped.

The check verifies the public runner-alive flag and configured limits. It
cannot certify broker connectivity, fills, protective orders or exit success.
Actual broker orders and positions remain in the authenticated dashboard,
which polls every five seconds while open and marks unsuccessful updates.
It does not generate trades to test the feed.

The independent email monitor also reads broker fills through the private
dashboard. See EMAIL-ALERTS.md. Notification checkpoints contain only exchange
session timestamps, incident timestamps and one-way event hashes, never
credentials, email addresses, symbols, order prices or quantities.

Limitations: GitHub schedules can be delayed or dropped, and public-repository
schedules are disabled after 60 days without repository activity. Render may
restart or suspend instances and shares 750 free instance hours across the
workspace. These checks reduce idle sleep, but do not guarantee availability,
fills, profit, the 01:25 IST exit, or uninterrupted dashboard updates. No paid
resource or billing upgrade is enabled. Failure status is visible in GitHub
Actions; email notifications depend on the user's existing GitHub settings.

Sources:
- https://render.com/docs/free
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job
