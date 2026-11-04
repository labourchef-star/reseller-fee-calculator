# Reseller Fee & Profit Calculator (US)
Free, no-signup calculator: fees, payout and profit on eBay, Poshmark, Mercari, Depop and Whatnot. Rates in `app/fees.py`, each with its official source URL and checked date.
Run: `uvicorn app.main:app`. Tests: `pytest`. Metrics: `GET /metrics` with `Authorization: Bearer $METRICS_TOKEN`. Own test hits: send `X-Test: 1`.
