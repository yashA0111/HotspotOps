import sys, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from diagnostics import _dns_query, http_probe, tcp_probe, tls_probe
from report import latency_statistics

class QualityTests(unittest.TestCase):
    def test_latency_statistics(self):
        stats=latency_statistics([10,20,30],3); self.assertEqual(stats["median_ms"],20); self.assertEqual(stats["packet_loss_percent"],0)
    def test_empty_statistics_marks_loss(self): self.assertEqual(latency_statistics([],3)["packet_loss_percent"],100)
    def test_dns_timeout_error_is_typed(self):
        _,category,_=_dns_query("example.com","192.0.2.1",1,.01); self.assertIn(category,{"timeout","dns_error"})
    @patch("diagnostics.socket.create_connection", side_effect=ConnectionRefusedError("refused"))
    def test_tcp_refusal_is_typed(self, _):
        result,_=tcp_probe("example.com",443,1,.1); self.assertEqual(result["error_category"],"connection_refused")
    @patch("diagnostics.ssl.create_default_context")
    @patch("diagnostics.socket.create_connection", side_effect=TimeoutError("timeout"))
    def test_tls_timeout_is_typed(self, _, __):
        result,_=tls_probe("example.com",443,1,.1); self.assertEqual(result["error_category"],"timeout")
    @patch("diagnostics.http.client.HTTPSConnection", side_effect=TimeoutError("timeout"))
    def test_http_timeout_is_typed(self, _):
        result,_=http_probe("https://example.com",1,.1); self.assertEqual(result["error_category"],"timeout")
