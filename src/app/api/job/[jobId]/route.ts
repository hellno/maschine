import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_API_KEY!
);

export async function GET(
  request: NextRequest,
  context: { params: { jobId: string } }
) {
  try {
    const { jobId } = context.params;
    
    if (!jobId) {
      return NextResponse.json({ error: 'Job ID is required' }, { status: 400 });
    }

    console.log('Getting job:', jobId);
  
    const { data, error } = await supabase
      .from('jobs')
      .select(`
        *,
        logs:logs(*)
      `)
      .eq('id', jobId)
      .order('created_at', { foreignTable: 'logs', ascending: true })
      .single();

    if (error) {
      console.error('Error fetching job:', error);
      return NextResponse.json({ error: 'Error fetching job' }, { status: 500 });
    }

    if (!data) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 });
    }

    return NextResponse.json({
      status: data.status,
      logs: data.logs || [],
      error: data.data?.error,
      createdAt: data.created_at,
      updatedAt: data.updated_at
    });
    
  } catch (error) {
    console.error('Error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
