import { NextResponse } from "next/server";
import { classifyReport } from "@/lib/diagnostics/engine";
import { reportSchema } from "@/lib/diagnostics/schema";

export async function POST(request: Request) {
  let body: unknown;
  try { body=await request.json(); } catch { return NextResponse.json({error:"Expected a JSON diagnostic report."},{status:400}); }
  const parsed=reportSchema.safeParse(body);
  if(!parsed.success) return NextResponse.json({error:"Report validation failed.",issues:parsed.error.flatten()},{status:422});
  return NextResponse.json({source:"LIVE_AGENT",report:parsed.data,findings:classifyReport(parsed.data)});
}
