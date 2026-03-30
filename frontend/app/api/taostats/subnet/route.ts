import { NextResponse } from "next/server";

const TAOSTATS_BASE = "https://api.taostats.io";
const NETUID = 26;

export async function GET() {
  const apiKey = process.env.TAOSTATS_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: "TAOSTATS_API_KEY not configured" },
      { status: 500 }
    );
  }

  try {
    const res = await fetch(
      `${TAOSTATS_BASE}/api/subnet/latest/v1?netuid=${NETUID}&network=test`,
      {
        headers: {
          Authorization: apiKey,
          Accept: "application/json",
        },
        next: { revalidate: 60 },
      }
    );

    if (!res.ok) {
      return NextResponse.json(
        { error: `Taostats API returned ${res.status}` },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json(
      { error: "Failed to reach Taostats API" },
      { status: 502 }
    );
  }
}
