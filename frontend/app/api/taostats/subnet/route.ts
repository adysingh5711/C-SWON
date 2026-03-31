const TAOSTATS_BASE = "https://api.taostats.io";
const NETUID = 26;

export const revalidate = 60;

export async function GET() {
  const apiKey = process.env.TAOSTATS_API_KEY;
  if (!apiKey) {
    return Response.json(
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
      }
    );

    if (!res.ok) {
      return Response.json(
        { error: `Taostats API returned ${res.status}` },
        { status: res.status }
      );
    }

    const data = await res.json();
    return Response.json(data);
  } catch {
    return Response.json(
      { error: "Failed to reach Taostats API" },
      { status: 502 }
    );
  }
}
