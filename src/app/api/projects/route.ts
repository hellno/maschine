/* eslint-disable @typescript-eslint/no-explicit-any */
import { NextResponse } from "next/server";
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_API_KEY!
);

const selectQuery = '*, jobs:jobs(*, logs:logs(*))';
export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const fid = url.searchParams.get("fid");
    const id = url.searchParams.get("id");

    console.log('Fetching projects:', { fid, id });
    if (!fid && !id) {
      return NextResponse.json({ error: "fid or id is required" }, { status: 400 });
    }

    let res;
    if (fid) {
      res = await supabase
        .from('projects')
        .select(selectQuery)
        .eq('fid_owner', Number(fid))
        .order('created_at', { ascending: false })
        .limit(10);
    } else {
      res = await supabase
        .from('projects')
        .select(selectQuery)
        .eq('id', id)
        .order('created_at', { ascending: false })
        .limit(10);
    }
    const { data: projects, error } = res;
    if (error) {
      console.error('Error fetching projects:', error);
      return NextResponse.json({ error: 'Error fetching projects' }, { status: 500 });
    }

    return NextResponse.json({ projects: projects || [] });
  } catch (error) {
    console.error("Error fetching projects:", error);
    return NextResponse.json(
      { error: "Failed to fetch projects" },
      { status: 500 }
    );
  }
}
