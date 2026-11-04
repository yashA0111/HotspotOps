import { Activity, AlertCircle, Bot, FileText, LayoutDashboard, Wifi } from "lucide-react";

export type Health = "Healthy" | "Degraded" | "Offline";
export type View = "Overview" | "Hotspots" | "Diagnostics" | "Incidents" | "AI Copilot" | "Reports";
export type Hotspot = { id:string; place:string; ap:string; state:Health; latency:number|null; loss:number|null; checked:string; city:string };
export type Incident = { id:string; title:string; place:string; hotspot:string; severity:"High"|"Medium"|"Low"; status:"Open"|"Acknowledged"|"Assigned"|"Resolved"; detected:string; layer:string; evidence:string; impact:string };

export const disclaimer="HotspotOps is an independent product concept and is not affiliated with or endorsed by DoT, C-DOT, TRAI or the Government of India. The public demo uses synthetic data and is not connected to live PM-WANI infrastructure.";
export const nav: {label:View; icon:typeof LayoutDashboard}[]=[{label:"Overview",icon:LayoutDashboard},{label:"Hotspots",icon:Wifi},{label:"Diagnostics",icon:Activity},{label:"Incidents",icon:AlertCircle},{label:"AI Copilot",icon:Bot},{label:"Reports",icon:FileText}];
export const hotspots:Hotspot[]=Array.from({length:24},(_,i)=>{const id=i+1; const states:Health[]=id===3?["Offline"]:([8,14,21].includes(id)?["Degraded"]:["Healthy"]); const place=id===3?"North Park Pavilion":id===8?"Market Street":id===14?"Civic Centre":id===21?"East Terminal":["Civic Centre","Riverfront Library","Market Street","West Transit Hub","Community Hall","North Park Pavilion","Arts Quarter","Old Town Exchange","Central Clinic","East Terminal","College Avenue","Harbour Walk"][i%12]; return {id:`HS-${String(id).padStart(3,"0")}`,place,ap:`AP-${String(201+id).padStart(3,"0")}`,state:states[0],latency:id===8?182:id===14?96:id===21?118:id===3?null:24+(id*13)%29,loss:id===8?4.8:id===14?3.2:id===21?1.2:id===3?null:(id*7)%6/10,checked:id===3?"12 min ago":`${1+(id%8)} min ago`,city:["North District","River District","Central District","East District"][i%4]};});
export const initialIncidents:Incident[]=[{id:"INC-2408",title:"DNS resolution failures",place:"Market Street, sample",hotspot:"HS-008",severity:"High",status:"Open",detected:"4 min ago",layer:"DNS",evidence:"DNS query timeout · 2,840 ms vs 46 ms baseline",impact:"External application checks blocked"},{id:"INC-2414",title:"Elevated packet loss",place:"Civic Centre, sample",hotspot:"HS-014",severity:"Medium",status:"Acknowledged",detected:"18 min ago",layer:"Quality",evidence:"Packet loss 3.2% · baseline 0.4%",impact:"Service quality degraded"},{id:"INC-2421",title:"Portal endpoint timeout",place:"East Terminal, sample",hotspot:"HS-021",severity:"Medium",status:"Open",detected:"31 min ago",layer:"Captive portal",evidence:"Portal response timeout · basic DNS passes",impact:"Portal test flow unavailable"},{id:"INC-2403",title:"AP heartbeat missing",place:"North Park Pavilion, sample",hotspot:"HS-003",severity:"High",status:"Open",detected:"12 min ago",layer:"Access point",evidence:"Simulated AP heartbeat absent for 12 min",impact:"Client association not available"}];
export const scenarios=["DNS resolver failure","Upstream / ISP degradation","Access point offline","Captive portal unavailable","Congestion / degraded quality"];
export const median=(values:number[])=>{const sorted=[...values].sort((a,b)=>a-b);const middle=Math.floor(sorted.length/2);return sorted.length%2?sorted[middle]:(sorted[middle-1]+sorted[middle])/2};
export const dnsBaseline=[42,48,44,51,46,39,54,45,47,49,46];
export const dnsCurrent=2840;
export const dnsMedian=median(dnsBaseline);
export const dnsMad=median(dnsBaseline.map(value=>Math.abs(value-dnsMedian)));
export const dnsThreshold=dnsMedian+3*dnsMad;
export const dnsAnomalous=dnsCurrent>dnsThreshold;
export const normalLatencyBaseline=[39,42,40,45,43,38,44,41,46,42,40];
export const normalLatencyCurrent=37;
export const normalLatencyMedian=median(normalLatencyBaseline);
export const normalLatencyMad=median(normalLatencyBaseline.map(value=>Math.abs(value-normalLatencyMedian)));
export const normalLatencyWithinRange=normalLatencyCurrent<=normalLatencyMedian+3*normalLatencyMad;
