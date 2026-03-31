const TAOSTATS_BASE = "https://api.taostats.io";
const NETUID = 26;

export const revalidate = 60;

export async function GET() {
  const apiKey = process.env.TAOSTATS_API_KEY;
  if (!apiKey || apiKey === "your-api-key-here") {
    return Response.json(
      { error: "TAOSTATS_API_KEY not configured. Get a free key at taostats.io and set it in .env.local" },
      { status: 503 }
    );
  }

  try {
    const res = await fetch(
      `${TAOSTATS_BASE}/api/metagraph/latest/v1?netuid=${NETUID}&network=test`,
      {
        headers: {
          Authorization: apiKey,
          Accept: "application/json",
        },
      }
    );

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      const msg = (body as Record<string, string>).message || `Taostats API returned ${res.status}`;
      return Response.json({ error: msg }, { status: res.status });
    }

    const data = await res.json();
    return Response.json(data);
  } catch {
    return Response.json(
      { error: "Failed to reach Taostats API — check your network connection" },
      { status: 502 }
    );
  }
}
