import { NextResponse } from "next/server";
import { getUserProjects } from "~/lib/kv";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const fid = url.searchParams.get("fid");

    if (!fid) {
      return NextResponse.json({ error: "FID is required" }, { status: 400 });
    }

    const projects = await getUserProjects(Number(fid));
    return NextResponse.json({ projects });
  } catch (error) {
    console.error("Error fetching projects:", error);
    return NextResponse.json(
      { error: "Failed to fetch projects" },
      { status: 500 }
    );
  }
}
