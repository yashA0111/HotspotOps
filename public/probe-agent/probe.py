from __future__ import annotations
import argparse, platform
from config import ProbeConfig
from diagnostics import dns_probe, gateway_probe, http_probe, route_probe, tcp_probe, tls_probe
from network import network_configuration
from report import measurement, new_report, write_report

def main() -> int:
    parser=argparse.ArgumentParser(description="HotspotOps bounded network diagnostic probe")
    parser.add_argument("--output",default="hotspotops-report.json"); parser.add_argument("--alternative-dns",action="append",default=[]); parser.add_argument("--endpoint",action="append",default=[]); parser.add_argument("--captive-url"); parser.add_argument("--attempts",type=int,default=3); parser.add_argument("--timeout",type=float,default=3.0); parser.add_argument("--max-hops",type=int,default=12)
    args=parser.parse_args(); config=ProbeConfig(attempts=max(1,min(args.attempts,5)),timeout_seconds=max(.5,min(args.timeout,10)),endpoints=tuple((args.endpoint or ProbeConfig.endpoints)[:5]),alternative_dns=tuple(args.alternative_dns[:3]),captive_url=args.captive_url,max_hops=max(1,min(args.max_hops,20)))
    network=network_configuration(); report=new_report(network,platform.platform())
    if network["warnings"]: report["results"].append(measurement("interface-config","interface",network["active_interface"] or "unidentified","configuration","warning" if network["addresses"] else "fail",None,"network_unavailable" if not network["addresses"] else "none",details={"warnings":network["warnings"]}))
    else: report["results"].append(measurement("interface-config","interface",network["active_interface"] or "active","configuration","pass",None,details={"addresses":network["addresses"]}))
    gateway,stats=gateway_probe(network["default_gateway"],config.attempts,config.timeout_seconds); report["results"].extend(gateway); report["statistics"].update(stats)
    dns,dns_stats=dns_probe(network["dns_servers"],list(config.alternative_dns),config.attempts,config.timeout_seconds); report["results"].extend(dns); report["statistics"].update(dns_stats)
    for url in config.endpoints:
        from urllib.parse import urlparse
        parsed=urlparse(url); host=parsed.hostname
        if not host: continue
        port=parsed.port or (443 if parsed.scheme=="https" else 80); tcp,tcp_stats=tcp_probe(host,port,config.attempts,config.timeout_seconds); report["results"].append(tcp); report["statistics"][tcp["id"]]=tcp_stats
        if parsed.scheme=="https": tls,tls_stats=tls_probe(host,port,config.attempts,config.timeout_seconds); report["results"].append(tls); report["statistics"][tls["id"]]=tls_stats
        http,http_stats=http_probe(url,config.attempts,config.timeout_seconds); report["results"].append(http); report["statistics"][http["id"]]=http_stats
    if config.captive_url:
        portal,portal_stats=http_probe(config.captive_url,config.attempts,config.timeout_seconds,"captive_portal"); report["results"].append(portal); report["statistics"][portal["id"]]=portal_stats
    report["traceroute"]=route_probe(config.traceroute_target,config.max_hops)
    path=write_report(report,args.output); print(f"HotspotOps report written to {path}"); return 0
if __name__=="__main__": raise SystemExit(main())
