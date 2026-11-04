import { z } from "zod";

export const resultStatus = z.enum(["pass", "fail", "warning", "blocked", "not_run"]);
export const errorCategory = z.enum(["none", "timeout", "connection_refused", "dns_nxdomain", "dns_servfail", "dns_error", "tls_certificate", "tls_handshake", "http_unexpected", "redirect", "icmp_restricted", "network_unavailable", "utility_unavailable", "unknown"]);

export const measurementSchema = z.object({
  id: z.string().min(1).max(128), timestamp_utc: z.string().datetime(), stage: z.enum(["interface", "gateway", "dns", "tcp", "tls", "http", "route", "captive_portal"]), target: z.string().min(1).max(512), protocol: z.string().min(1).max(32), result: resultStatus, duration_ms: z.number().nonnegative().nullable(), error_category: errorCategory, error_detail: z.string().max(1000).optional(), attempts: z.number().int().min(0).max(20), successful_attempts: z.number().int().min(0).max(20), failed_attempts: z.number().int().min(0).max(20), details: z.record(z.string(), z.unknown()).default({}),
});

export const reportSchema = z.object({
  schema_version: z.literal("1.0"), session_id: z.string().uuid(), collected_at_utc: z.string().datetime(), probe: z.object({ os: z.string().max(120), hostname: z.string().max(255).optional(), version: z.string().max(64) }),
  network_configuration: z.object({ active_interface: z.string().max(255).nullable(), interface_type: z.enum(["wifi", "ethernet", "unknown"]), addresses: z.array(z.string().max(128)).max(20), default_gateway: z.string().max(128).nullable(), dns_servers: z.array(z.string().max(128)).max(12), default_route: z.string().max(512).nullable(), warnings: z.array(z.string().max(500)).max(20) }),
  results: z.array(measurementSchema).min(1).max(300), statistics: z.record(z.string(), z.object({ minimum_ms: z.number().nullable(), median_ms: z.number().nullable(), maximum_ms: z.number().nullable(), mean_ms: z.number().nullable(), packet_loss_percent: z.number().min(0).max(100).nullable() })).default({}),
  traceroute: z.array(z.object({ hop: z.number().int().positive(), address: z.string().nullable(), duration_ms: z.number().nullable(), status: z.enum(["response", "timeout", "unavailable"]) })).max(40).default([]),
});

export type DiagnosticReport = z.infer<typeof reportSchema>;
export type Measurement = z.infer<typeof measurementSchema>;
