import { createClient } from '@supabase/supabase-js';
import { NextResponse } from 'next/server';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_API_KEY!
);

export async function POST(request: Request) {
  try {
    const { projectId } = await request.json();
    
    if (!projectId) {
      return NextResponse.json({ error: 'Project ID is required' }, { status: 400 });
    }

    const { data, error } = await supabase
      .from('projects')
      .update({ frame_pinned_count: supabase.sql`frame_pinned_count + 1` })
      .eq('id', projectId)
      .select('frame_pinned_count')
      .single();

    if (error) {
      console.error('Error incrementing pin count:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json({ frame_pinned_count: data.frame_pinned_count });
  } catch (error) {
    console.error('Error in increment-frame-pins:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
