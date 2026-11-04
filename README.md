# HotspotOps

An independent public Wi-Fi service-assurance concept, with a public product site and a synthetic interactive operations console.

## Run locally

Requires Node.js 20.9 or later.

```bash
npm install
npm run dev
```

Open `http://localhost:3000` for the product site or `http://localhost:3000/demo` for the console.

## Demo contents

- Synthetic fleet overview, hotspot inventory and illustrative availability history.
- Five diagnostic scenario replays with dependency-aware results.
- Incident review and local acknowledge, assign and resolve actions.
- A median/MAD statistical threshold over synthetic sample telemetry.
- A deterministic, scenario-grounded Copilot preview with unsupported-question handling.
- CSV export of the visible sample hotspot records.
- A downloadable Python Probe Agent that captures bounded, real network-path measurements and outputs an uploadable JSON report.
- Server-side Zod validation and evidence-based reclassification for uploaded `LIVE_AGENT` reports.

There is no live network connection, external AI service, PM-WANI integration, production probe or persistent backend. Browser-only operational changes reset on refresh. The footer on both routes contains the complete independence and synthetic-data disclosure.

## Live diagnostic reports

The downloadable `probe-agent/` runs locally on a Windows or Linux computer connected to the investigated network. Its data collection is real and bounded; the public demo remains synthetic until a visitor uploads that report. The server validates the report and recalculates every finding from raw measurements. See [probe-agent/README.md](probe-agent/README.md) for execution and privacy boundaries.
