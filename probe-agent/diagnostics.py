from __future__ import annotations
import http.client, os, platform, random, re, socket, ssl, struct, time
from urllib.parse import urlparse
from typing import Any
from network import safe_run
from report import measurement, latency_statistics

def gateway_probe(gateway: str | None, attempts: int, timeout: float) -> tuple[list[dict], dict]:
    if not gateway: return [measurement("gateway-config", "gateway", "default gateway", "icmp", "blocked", None, "network_unavailable", attempts=0, details={"reason":"No default gateway configured"})], {}
    command = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), gateway] if platform.system() == "Windows" else ["ping", "-c", "1", "-W", str(max(1, int(timeout))), gateway]
    samples=[]; failures=[]
    for index in range(attempts):
        code, out, err = safe_run(command, timeout + 2)
        match=re.search(r"(?:time[=<])\s*([\d.]+)\s*ms", out, re.I)
        if code == 0 and match: samples.append(float(match.group(1)))
        else: failures.append(err or out[-200:] or "no ICMP reply")
    status="pass" if samples else "fail"; category="none" if samples else "icmp_restricted"
    result=measurement("gateway-icmp", "gateway", gateway, "icmp", status, latency_statistics(samples, attempts)["median_ms"], category, attempts=attempts, successful_attempts=len(samples), failed_attempts=attempts-len(samples), details={"samples_ms":samples,"note":"ICMP may be restricted; absent replies alone do not confirm gateway failure."}, error_detail=failures[0] if failures else None)
    return [result], {"gateway_icmp":latency_statistics(samples, attempts)}

def _dns_query(name: str, resolver: str, qtype: int, timeout: float) -> tuple[float | None, str, str | None]:
    transaction=random.randint(0, 65535); header=struct.pack("!HHHHHH", transaction, 0x0100, 1, 0, 0, 0); question=b"".join(bytes([len(part)])+part.encode("idna") for part in name.split("."))+b"\x00"+struct.pack("!HH",qtype,1)
    family=socket.AF_INET6 if ":" in resolver else socket.AF_INET
    started=time.monotonic()
    try:
        with socket.socket(family, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout); sock.sendto(header+question,(resolver,53)); data,_=sock.recvfrom(4096)
        if len(data)<12: return None,"dns_error","short DNS response"
        received,flags,_,answers,_,_=struct.unpack("!HHHHHH",data[:12])
        if received != transaction: return None,"dns_error","mismatched DNS transaction"
        rcode=flags & 0xF; error={0:None,2:"dns_servfail",3:"dns_nxdomain"}.get(rcode,"dns_error" if rcode else None)
        return (time.monotonic()-started)*1000, error or "none", f"rcode={rcode}; answers={answers}" if error else f"answers={answers}"
    except socket.timeout: return None,"timeout","DNS query timed out"
    except OSError as exc: return None,"dns_error",str(exc)

def dns_probe(resolvers: list[str], alternatives: list[str], attempts: int, timeout: float) -> tuple[list[dict],dict]:
    results=[]; stats={}
    for resolver, role in [(value,"configured") for value in resolvers]+[(value,"alternative") for value in alternatives]:
        for record, qtype in [("A",1),("AAAA",28)]:
            durations=[]; errors=[]
            for _ in range(attempts):
                duration, category, detail=_dns_query("example.com",resolver,qtype,timeout)
                if duration is not None and category=="none": durations.append(duration)
                else: errors.append((category,detail))
            category=errors[0][0] if errors else "none"; status="pass" if durations else "fail"
            ident=f"dns-{role}-{resolver.replace(':','_')}-{record.lower()}"; results.append(measurement(ident,"dns",resolver,"dns",status,latency_statistics(durations,attempts)["median_ms"],category,attempts=attempts,successful_attempts=len(durations),failed_attempts=attempts-len(durations),details={"resolver_role":role,"record_type":record,"query_name":"example.com","samples_ms":durations},error_detail=errors[0][1] if errors else None)); stats[ident]=latency_statistics(durations,attempts)
    return results,stats

def tcp_probe(host: str, port: int, attempts: int, timeout: float) -> tuple[dict,dict]:
    durations=[]; categories=[]; details=[]
    for _ in range(attempts):
        started=time.monotonic()
        try:
            with socket.create_connection((host,port),timeout=timeout): durations.append((time.monotonic()-started)*1000)
        except socket.gaierror as exc: categories.append("dns_error");details.append(str(exc))
        except ConnectionRefusedError as exc: categories.append("connection_refused");details.append(str(exc))
        except TimeoutError as exc: categories.append("timeout");details.append(str(exc))
        except OSError as exc: categories.append("unknown");details.append(str(exc))
    stat=latency_statistics(durations,attempts); category=categories[0] if categories else "none"; return measurement(f"tcp-{host}-{port}","tcp",f"{host}:{port}","tcp","pass" if durations else "fail",stat["median_ms"],category,attempts=attempts,successful_attempts=len(durations),failed_attempts=attempts-len(durations),details={"samples_ms":durations},error_detail=details[0] if details else None),stat

def tls_probe(host: str, port: int, attempts: int, timeout: float) -> tuple[dict,dict]:
    durations=[]; categories=[]; details=[]; expires=[]; context=ssl.create_default_context()
    for _ in range(attempts):
        started=time.monotonic()
        try:
            with socket.create_connection((host,port),timeout=timeout) as raw:
                with context.wrap_socket(raw,server_hostname=host) as secured:
                    durations.append((time.monotonic()-started)*1000); expires.append(secured.getpeercert().get("notAfter"))
        except ssl.SSLCertVerificationError as exc: categories.append("tls_certificate");details.append(str(exc))
        except ssl.SSLError as exc: categories.append("tls_handshake");details.append(str(exc))
        except (OSError,TimeoutError) as exc: categories.append("timeout" if isinstance(exc,TimeoutError) else "unknown");details.append(str(exc))
    stat=latency_statistics(durations,attempts); category=categories[0] if categories else "none"; return measurement(f"tls-{host}-{port}","tls",f"{host}:{port}","tls","pass" if durations else "fail",stat["median_ms"],category,attempts=attempts,successful_attempts=len(durations),failed_attempts=attempts-len(durations),details={"samples_ms":durations,"certificate_expiry":expires[0] if expires else None,"verification":"enabled"},error_detail=details[0] if details else None),stat

def http_probe(url: str, attempts: int, timeout: float, stage: str="http") -> tuple[dict,dict]:
    durations=[]; errors=[]; statuses=[]; redirects=[]; parsed=urlparse(url); host=parsed.hostname or ""; port=parsed.port or (443 if parsed.scheme=="https" else 80)
    for _ in range(attempts):
        started=time.monotonic()
        try:
            connection=(http.client.HTTPSConnection(host,port,timeout=timeout,context=ssl.create_default_context()) if parsed.scheme=="https" else http.client.HTTPConnection(host,port,timeout=timeout))
            connection.request("GET",parsed.path or "/",headers={"User-Agent":"HotspotOps-Probe/1.0","Accept":"*/*"}); response=connection.getresponse(); duration=(time.monotonic()-started)*1000; statuses.append(response.status); redirects.append(response.getheader("Location")); response.read(1024); connection.close(); durations.append(duration)
        except socket.gaierror as exc: errors.append(("dns_error",str(exc)))
        except ssl.SSLCertVerificationError as exc: errors.append(("tls_certificate",str(exc)))
        except ssl.SSLError as exc: errors.append(("tls_handshake",str(exc)))
        except (TimeoutError,socket.timeout) as exc: errors.append(("timeout",str(exc)))
        except OSError as exc: errors.append(("unknown",str(exc)))
    stat=latency_statistics(durations,attempts); expected=200<=statuses[0]<400 if statuses else False; redirect=bool(redirects and redirects[0]); category="redirect" if stage=="captive_portal" and redirect else (errors[0][0] if errors else ("none" if expected else "http_unexpected")); result="warning" if stage=="captive_portal" and redirect else ("pass" if expected else "fail")
    return measurement(f"{stage}-{host}-{port}",stage,url,"https" if parsed.scheme=="https" else "http",result,stat["median_ms"],category,attempts=attempts,successful_attempts=len(durations),failed_attempts=attempts-len(durations),details={"status_codes":statuses,"redirect_location":redirects[0] if redirects else None,"expected":"2xx or 3xx"},error_detail=errors[0][1] if errors else None),stat

def route_probe(target: str, max_hops: int) -> list[dict]:
    command=["tracert","-d","-h",str(max_hops),target] if platform.system()=="Windows" else ["traceroute","-n","-m",str(max_hops),target]
    code,out,error=safe_run(command, max_hops*2+5)
    if code is None: return [{"hop":1,"address":None,"duration_ms":None,"status":"unavailable"}]
    hops=[]
    for line in out.splitlines():
        match=re.match(r"\s*(\d+)\s+(.*)",line)
        if not match: continue
        hop=int(match.group(1)); body=match.group(2); address_match=re.search(r"(?:\d{1,3}\.){3}\d{1,3}|[0-9a-fA-F:]{3,}",body); time_match=re.search(r"(\d+(?:\.\d+)?)\s*ms",body)
        hops.append({"hop":hop,"address":address_match.group(0) if address_match else None,"duration_ms":float(time_match.group(1)) if time_match else None,"status":"response" if address_match else "timeout"})
    return hops or [{"hop":1,"address":None,"duration_ms":None,"status":"unavailable"}]
