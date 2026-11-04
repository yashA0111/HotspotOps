import { describe, expect, it } from "vitest";
import { classifyReport } from "./engine";
import type { DiagnosticReport } from "./schema";

const base: DiagnosticReport = {
  schema_version:"1.0", session_id:"9bbfb5fd-3877-4c84-a84f-4ebd61ee29c9", collected_at_utc:"2026-11-05T10:00:00Z", probe:{os:"test",version:"1.0.0"}, network_configuration:{active_interface:"eth0",interface_type:"ethernet",addresses:["192.0.2.10/24"],default_gateway:"192.0.2.1",dns_servers:["192.0.2.53"],default_route:"default via 192.0.2.1",warnings:[]}, results:[], statistics:{}, traceroute:[],
};
const result=(id:string,stage:DiagnosticReport["results"][number]["stage"],outcome:DiagnosticReport["results"][number]["result"],details:Record<string,unknown>={},error_category:DiagnosticReport["results"][number]["error_category"]="none"):DiagnosticReport["results"][number]=>({id,timestamp_utc:"2026-11-05T10:00:00Z",stage,target:"example.test",protocol:"test",result:outcome,duration_ms:20,error_category,attempts:3,successful_attempts:outcome==="pass"?3:0,failed_attempts:outcome==="pass"?0:3,details});

describe("classifyReport",()=>{
  it("identifies a configured resolver problem only when comparison evidence passes",()=>{
    const report={...base,results:[result("gateway","gateway","pass"),result("dns-config","dns","fail",{resolver_role:"configured"},"timeout"),result("dns-alt","dns","pass",{resolver_role:"alternative"})]};
    expect(classifyReport(report).some(finding=>finding.domain==="dns_resolver"&&finding.confidence==="high")).toBe(true);
  });
  it("does not label a single destination failure as broad upstream degradation",()=>{
    const report={...base,results:[result("gateway","gateway","pass"),result("tcp-a","tcp","fail",{},"timeout"),result("tcp-b","tcp","pass")]};
    const findings=classifyReport(report); expect(findings.some(finding=>finding.domain==="destination_specific")).toBe(true); expect(findings.some(finding=>finding.domain==="upstream_connectivity")).toBe(false);
  });
  it("keeps certificate failure distinct from transport failure",()=>{
    const report={...base,results:[result("tcp","tcp","pass"),result("tls","tls","fail",{},"tls_certificate")]};
    expect(classifyReport(report).some(finding=>finding.domain==="tls_certificate")).toBe(true);
  });
});
