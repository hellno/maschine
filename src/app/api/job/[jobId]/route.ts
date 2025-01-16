import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_API_KEY!
);


export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  try {
    const { jobId } = await params;

    // Validate jobId presence
    if (!jobId) {
      return NextResponse.json(
        { error: 'Job ID is required' },
        { status: 400 }
      );
    }

    console.log('Fetching job with ID:', jobId);

    // Fetch job data along with associated logs from Supabase
    const { data, error } = await supabase
      .from('jobs')
      .select(`
        *,
        logs:logs(*)
      `)
      .eq('id', jobId)
      .order('created_at', { foreignTable: 'logs', ascending: true })
      .single();

    // Handle Supabase errors
    if (error) {
      console.error('Supabase error:', error.message);
      return NextResponse.json(
        { error: 'Error fetching job data' },
        { status: 500 }
      );
    }

    // Handle case where no data is returned
    if (!data) {
      return NextResponse.json(
        { error: 'Job not found' },
        { status: 404 }
      );
    }

    // Construct and return the response
    return NextResponse.json({
      status: data.status,
      logs: data.logs || [],
      createdAt: data.created_at,
      updatedAt: data.updated_at
    });

  } catch (error) {
    // Handle unexpected errors
    console.error('Unexpected error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}