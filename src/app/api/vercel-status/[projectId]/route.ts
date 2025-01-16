import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { VercelLogData } from '~/lib/types';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_API_KEY!
);

async function getDeploymentLogs(deploymentId: string) {
  try {
    const response = await fetch(
      `https://api.vercel.com/v2/deployments/${deploymentId}/events`,
      {
        headers: {
          Authorization: `Bearer ${process.env.VERCEL_TOKEN}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch logs: ${response.statusText}`);
    }

    const data = await response.json();
    return data || [];
  } catch (error) {
    console.error('Failed to fetch deployment logs:', error);
    return [];
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ projectId: string }> }
) {
  try {
    const { projectId } = await params;

    // Get project's Vercel project ID from your DB
    const { data: project, error: projectError } = await supabase
      .from('projects')
      .select('vercel_project_id')
      .eq('id', projectId)
      .single();

    if (projectError || !project?.vercel_project_id) {
      return NextResponse.json(
        { error: "Project not found" },
        { status: 404 }
      );
    }

    // Get latest deployment using v6 API
    const response = await fetch(
      `https://api.vercel.com/v6/deployments?projectId=${project.vercel_project_id}&teamId=${process.env.VERCEL_TEAM_ID}&limit=1`,
      {
        headers: {
          Authorization: `Bearer ${process.env.VERCEL_TOKEN}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Vercel API error: ${response.statusText}`);
    }

    const data = await response.json();
    const latestDeployment = data.deployments?.[0];

    if (!latestDeployment) {
      return NextResponse.json(
        { error: "No deployments found" },
        { status: 404 }
      );
    }

    // Get deployment logs
    const deploymentLogs = await getDeploymentLogs(latestDeployment.uid);
    // Format logs to match your frontend Log type
    const formattedLogs = deploymentLogs.map((event: {
      id: string;
      createdAt: string;
      message: string;
      type: string;
      payload: VercelLogData;
    }) => ({
      id: event.id,
      created_at: event.createdAt,
      source: 'vercel',
      text: event.message || event.type,
      type: event.type,
      payload: event.payload
    }));

    return NextResponse.json({
      status: latestDeployment.state,
      url: latestDeployment.url,
      createdAt: latestDeployment.createdAt,
      ready: latestDeployment.ready,
      buildingAt: latestDeployment.buildingAt,
      meta: {
        githubCommitRef: latestDeployment.meta?.githubCommitRef,
        githubCommitSha: latestDeployment.meta?.githubCommitSha,
      },
      logs: formattedLogs
    });

  } catch (error) {
    console.error('Error fetching Vercel status:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
