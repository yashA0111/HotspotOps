from dataclasses import dataclass, field

@dataclass(frozen=True)
class ProbeConfig:
    attempts: int = 3
    timeout_seconds: float = 3.0
    endpoints: tuple[str, ...] = ("https://example.com", "https://www.cloudflare.com/cdn-cgi/trace")
    alternative_dns: tuple[str, ...] = ()
    captive_url: str | None = None
    traceroute_target: str = "example.com"
    max_hops: int = 12
