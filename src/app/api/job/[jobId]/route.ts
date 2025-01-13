import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_API_KEY!
);

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

    console.log('Getting job:', jobId);
  
    // AI! simplify this code by using one supabase client function instead of two in a promise all 
  
    // Get job info and logs concurrently
    const [{ data: job, error: jobError }, { data: logs, error: logsError }] = await Promise.all([
      // Get job details
      supabase
        .from('jobs')
        .select('*')
        .eq('id', jobId)
        .single(),
      
      // Get job logs
      supabase
        .from('logs')
        .select('*')
        .eq('job_id', jobId)
        .order('created_at', { ascending: true })
    ]);

    if (jobError) {
      console.error('Error fetching job:', jobError);
      return NextResponse.json({ error: 'Error fetching job' }, { status: 500 });
    }

    if (logsError) {
      console.error('Error fetching logs:', logsError);
      return NextResponse.json({ error: 'Error fetching logs' }, { status: 500 });
    }

    if (!job) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 });
    }

    return NextResponse.json({
      status: job.status,
      logs: logs || [],
      error: job.data?.error,
      createdAt: job.created_at,
      updatedAt: job.updated_at
    });
    
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
