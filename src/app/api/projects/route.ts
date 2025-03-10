/* eslint-disable @typescript-eslint/no-explicit-any */
import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_API_KEY!,
);

const selectQuery = "*, jobs:jobs(*, logs:logs(*)), builds:builds(*)";
export async function DELETE(request: Request) {
  try {
    const { id } = await request.json();
    if (!id) {
      return NextResponse.json(
        { error: "Project ID is required" },
        { status: 400 },
      );
    }

    const { data, error } = await supabase
      .from("projects")
      .update({
        status: "removed",
      })
      .eq("id", id)
      .select();

    if (error) {
      console.error("Error soft deleting project:", error);
      return NextResponse.json(
        { error: "Error removing project" },
        { status: 500 },
      );
    }

    if (!data || data.length === 0) {
      return NextResponse.json({ error: "Project not found" }, { status: 404 });
    }

    return NextResponse.json({ project: data[0] });
  } catch (error) {
    console.error("Error removing project:", error);
    return NextResponse.json(
      { error: "Failed to remove project" },
      { status: 500 },
    );
  }
}

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
        .neq("status", "removed")
        .order("created_at", { ascending: false })
        .limit(10);
    } else {
      res = await supabase
        .from("projects")
        .select(selectQuery)
        .eq("id", id)
        .neq("status", "removed")
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
      const hasAnyJobsPending =
        latestJob?.status === "pending" ||
        latestJob?.status === "running" ||
        latestBuild?.status === "submitted" ||
        latestBuild?.status === "building" ||
        latestBuild?.status === "queued";

      return {
        ...project,
        latestJob,
        latestBuild,
        hasAnyJobsPending,
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
