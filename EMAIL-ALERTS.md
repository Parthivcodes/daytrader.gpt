# Free Daytrader email notifications

The market-hours GitHub workflow independently checks the authenticated
dashboard every five minutes. It does not require a running laptop or Codex.
The recipient, Resend API key and dashboard access code are encrypted Actions
secrets. No Alpaca order-placement credential is available to this monitor.

Alerts cover:
- Confirmed paper BUY and SELL cumulative fills, including protective exits.
- One offline/unhealthy alert per detected incident during the actual exchange
  session previously read from Alpaca's clock.
- One recovery alert when broker data and a fresh runner heartbeat return.

An accepted order without a fill does not generate a trade email. Multiple
partial executions between checks may appear as one cumulative-fill email.
The monitor retries a failed read once, suppresses repeats using hashed
checkpoints and Resend's 24-hour idempotency keys, and caps trade emails at
20 per UTC day. Fills from old sessions are not replayed after a cache loss.
Cache loss can cause repeated incident alerts; email delivery is best-effort.

The notification checkpoint uses GitHub Actions cache. Only exchange session
timestamps, incident timestamps and one-way event hashes are stored there.
It does not contain passwords, API keys, email addresses or trade details.

The sender is onboarding@resend.dev, allowed only to the Resend account's own
verified email address. Resend Free currently permits 100 emails/day and
3,000/month. No paid sender, domain, plan or billing upgrade is enabled.
The provider may reject messages at a quota limit; do not enable paid overages.

Outage detection depends on the independent GitHub schedule actually running.
No alert can be promised when GitHub is delayed, the email service fails, or
the initial successful exchange-session baseline has never been obtained.
Free Render hosting still has sleep, restart, and quota limitations.

Mail subjects identify PAPER BUY/SELL or offline/recovery. Details are emailed
only to the configured recipient; logs suppress private provider responses.
Sender acceptance does not prove delivery to the inbox; check spam for the
initial connection-test email.

Sources:
- https://resend.com/pricing
- https://resend.com/docs/dashboard/emails/idempotency-keys
- https://resend.com/docs/knowledge-base/403-error-resend-dev-domain
