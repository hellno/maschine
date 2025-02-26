/* eslint-disable @typescript-eslint/no-explicit-any */
import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_API_KEY!,
);

const selectQuery = "*, jobs:jobs(*, logs:logs(*)), builds:builds(*)";
export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const fid = url.searchParams.get("fid");
    const id = url.searchParams.get("id");

    console.log("Fetching projects:", { fid, id });
    if (!fid && !id) {
      return NextResponse.json(
        { error: "fid or id is required" },
        { status: 400 },
      );
    }

    let res;
    if (fid) {
      res = await supabase
        .from("projects")
        .select(selectQuery)
        .eq("fid_owner", Number(fid))
        .order("created_at", { ascending: false })
        .limit(10);
    } else {
      res = await supabase
        .from("projects")
        .select(selectQuery)
        .eq("id", id)
        .order("created_at", { ascending: false })
        .limit(10);
    }
    const { data: projects, error } = res;
    if (error) {
      console.error("Error fetching projects:", error);
      return NextResponse.json(
        { error: "Error fetching projects" },
        { status: 500 },
      );
    }

    // Enhance projects with latest_build and latest_job
    const enhancedProjects = projects?.map((project) => {
      const sortedJobs = project.jobs?.sort(
        (
          a: { created_at: string | number | Date },
          b: { created_at: string | number | Date },
        ) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      );
      const latestJob = sortedJobs?.length > 0 ? sortedJobs[0] : null;

      const sortedBuilds = project.builds?.sort(
        (
          a: { created_at: string | number | Date },
          b: { created_at: string | number | Date },
        ) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      );
      const latestBuild = sortedBuilds?.length > 0 ? sortedBuilds[0] : null;

      return {
        ...project,
        latestJob: latestJob,
        latestBuild: latestBuild,
      };
    });

    return NextResponse.json({ projects: enhancedProjects || [] });
  } catch (error) {
    console.error("Error fetching projects:", error);
    return NextResponse.json(
      { error: "Failed to fetch projects" },
      { status: 500 },
    );
  }
}
