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
