# HotspotOps Probe Agent

The Probe Agent performs real, bounded diagnostic measurements from the computer where it runs. It uses Python 3.10+ and the standard library only. It does not collect packet contents, credentials, browsing history, subscriber data, or perform authentication, scans, or configuration changes.

## Run

Windows PowerShell:

```powershell
python probe.py --output hotspotops-report.json
```

Linux:

```bash
python3 probe.py --output hotspotops-report.json
```

Optional explicit comparison DNS resolvers and test endpoints:

```bash
python3 probe.py --alternative-dns 1.1.1.1 --alternative-dns 8.8.8.8 --endpoint https://example.com --endpoint https://www.cloudflare.com/cdn-cgi/trace --captive-url http://connectivitycheck.gstatic.com/generate_204
```

The probe uses a maximum of three attempts per gateway and endpoint test, short timeouts, and two configured HTTPS endpoints by default. It does not disable certificate verification. It uses available operating-system utilities only for bounded `ping` and `traceroute`/`tracert` commands with fixed argument lists; missing utilities are reported in the JSON instead of treated as a failure.

`traceroute` results show responding and timed-out hops. Routers may suppress ICMP replies, so a timed-out hop does not prove loss.

## Upload

Open HotspotOps Console → Diagnostics → **Upload agent report**, choose the generated JSON file, and inspect the `LIVE_AGENT` session. The website validates the report and recalculates findings from measurements; it does not trust a diagnosis embedded in the file.

## Tests

```bash
python3 -m unittest discover -s tests -v
```
