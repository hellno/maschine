import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  try {
    const { prompt, userContext } = await request.json()
    
    // Validate input
    if (!prompt || !userContext) {
      return NextResponse.json(
        { error: 'Prompt and user context are required' },
        { status: 400 }
      )
    }

    // Get repo name from environment variables
    const repo = process.env.REPO_NAME
    if (!repo) {
      return NextResponse.json(
        { error: 'Repository not configured' },
        { status: 500 }
      )
    }

    // Call LLM manipulation endpoint
    const llmResponse = await fetch(process.env.LLM_MANIPULATION_ENDPOINT!, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        repo,
        prompt: `${prompt}\n\nUser Context: ${JSON.stringify(userContext)}`
      }),
    })

    if (!llmResponse.ok) {
      throw new Error(`LLM endpoint returned ${llmResponse.status}`)
    }

    const result = await llmResponse.json()
    
    return NextResponse.json(result)
    
  } catch (error) {
    console.error('Error in template customization:', error)
    return NextResponse.json(
      { error: 'Failed to customize template' },
      { status: 500 }
    )
  }
}
