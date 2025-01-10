import { NextResponse } from 'next/server';
import { getJob, getJobLogs } from '~/lib/kv';

export async function GET(
  request: Request,
  { params }: { params: { jobId: string } }
) {
  const { jobId } = params;
  
  try {
    const job = await getJob(jobId);
    if (!job) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 });
    }

    const logs = await getJobLogs(jobId);
    
    return NextResponse.json({
      status: job.status,
      logs,
      error: job.error,
      createdAt: job.createdAt,
      updatedAt: job.updatedAt
    });
    
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
import { NextResponse } from 'next/server';
import { getJob, getJobLogs } from '~/lib/kv';

export async function GET(
  request: Request,
  { params }: { params: { jobId: string } }
) {
  try {
    // Destructure jobId from params
    const { jobId } = params;
    
    if (!jobId) {
      return NextResponse.json({ error: 'Job ID is required' }, { status: 400 });
    }

    // Get job info and logs
    const [job, logs] = await Promise.all([
      getJob(jobId),
      getJobLogs(jobId)
    ]);

    if (!job) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 });
    }

    return NextResponse.json({
      status: job.status,
      logs,
      error: job.error,
      createdAt: job.createdAt,
      updatedAt: job.updatedAt
    });
    
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
import { NextResponse } from 'next/server';
import { getJob, getJobLogs } from '~/lib/kv';

export async function GET(
  request: Request,
  { params }: { params: { jobId: string } }
) {
  try {
    // Destructure jobId from params
    const { jobId } = params;
    
    if (!jobId) {
      return NextResponse.json({ error: 'Job ID is required' }, { status: 400 });
    }

    // Get job info and logs concurrently
    const [job, logs] = await Promise.all([
      getJob(jobId),
      getJobLogs(jobId)
    ]);

    if (!job) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 });
    }

    return NextResponse.json({
      status: job.status,
      logs,
      error: job.error,
      createdAt: job.createdAt,
      updatedAt: job.updatedAt
    });
    
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
