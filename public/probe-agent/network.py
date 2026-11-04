from __future__ import annotations
import ipaddress, platform, re, socket, subprocess
from pathlib import Path
from typing import Any

def safe_run(arguments: list[str], timeout: float = 5.0) -> tuple[int | None, str, str]:
    try:
        completed = subprocess.run(arguments, capture_output=True, text=True, timeout=timeout, check=False, shell=False)
        return completed.returncode, completed.stdout, completed.stderr
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return None, "", str(exc)

def _linux_config() -> dict[str, Any]:
    _, route, _ = safe_run(["ip", "route", "show", "default"])
    default_route = next((line for line in route.splitlines() if line.startswith("default")), None)
    gateway = re.search(r"via\s+(\S+)", default_route or "")
    interface = re.search(r"dev\s+(\S+)", default_route or "")
    name = interface.group(1) if interface else None
    _, addr, _ = safe_run(["ip", "-o", "addr", "show", "dev", name] if name else ["ip", "-o", "addr", "show"])
    addresses = [line.split()[3] for line in addr.splitlines() if len(line.split()) > 3 and line.split()[2] in ("inet", "inet6")]
    resolv = Path("/etc/resolv.conf")
    dns = [line.split()[1] for line in resolv.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip().startswith("nameserver") and len(line.split()) > 1] if resolv.exists() else []
    return {"active_interface": name, "interface_type": "wifi" if name and re.match(r"^(wl|wlan)", name) else "ethernet" if name and re.match(r"^(en|eth)", name) else "unknown", "addresses": addresses, "default_gateway": gateway.group(1) if gateway else None, "dns_servers": dns, "default_route": default_route, "warnings": []}

def _windows_config() -> dict[str, Any]:
    _, route, _ = safe_run(["route", "print", "-4"])
    route_line = next((line for line in route.splitlines() if re.match(r"\s*0\.0\.0\.0\s+0\.0\.0\.0", line)), None)
    parts = route_line.split() if route_line else []
    gateway = parts[2] if len(parts) > 3 else None
    _, output, _ = safe_run(["ipconfig", "/all"])
    dns = re.findall(r"DNS Servers[^\n]*:\s*([^\r\n]+)", output)
    dns_servers = [value.strip() for value in dns]
    addresses = re.findall(r"(?:IPv4 Address|IPv6 Address)[^:]*:\s*([^\s(]+)", output)
    active_name = None
    for block in re.split(r"\r?\n\r?\n", output):
        if gateway and gateway in block:
            match = re.search(r"(?:adapter )?([^:\r\n]+):", block, re.I)
            active_name = match.group(1).strip() if match else None
            break
    return {"active_interface": active_name, "interface_type": "wifi" if active_name and "wi-fi" in active_name.lower() else "ethernet" if active_name else "unknown", "addresses": addresses, "default_gateway": gateway, "dns_servers": dns_servers, "default_route": route_line.strip() if route_line else None, "warnings": []}

def network_configuration() -> dict[str, Any]:
    config = _windows_config() if platform.system() == "Windows" else _linux_config()
    if not config["active_interface"]: config["warnings"].append("No active default-route interface was identified.")
    if not config["addresses"]: config["warnings"].append("No assigned interface address was identified.")
    if not config["default_gateway"]: config["warnings"].append("No default gateway was identified.")
    if not config["dns_servers"]: config["warnings"].append("No configured DNS resolver was identified.")
    return config

def resolve_numeric(host: str) -> str | None:
    try: return str(ipaddress.ip_address(host))
    except ValueError: return None
