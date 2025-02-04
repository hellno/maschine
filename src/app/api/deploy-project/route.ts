import { NextResponse, NextRequest } from "next/server";

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const DEPLOY_PROJECT_ENDPOINT = 'https://herocast--deploy-project-webhook.modal.run';

export const config = {
  maxDuration: 60,
};

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { projectId, userContext } = body;

    if (!projectId || !userContext) {
      return NextResponse.json(
        { error: "projectId and user_context are required" },
        { status: 400 }
      );
    }

    const response = await fetch(DEPLOY_PROJECT_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        project_id: projectId,
        user_context: userContext
      })
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error deploying project:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Deployment failed' },
      { status: 500 }
    );
  }
}
