import { NextResponse } from 'next/server'

const LLM_MANIPULATION_ENDPOINT = 'https://herocast--update-code.modal.run';

export async function POST(request: Request) {
  try {
    const { repoPath, prompt, userContext } = await request.json()

    // Validate input
    if (!repoPath || !prompt || !userContext) {
      return NextResponse.json(
        { error: 'Repo, prompt and user context are required' },
        { status: 400 }
      )
    }

    console.log('received request:', { repoPath, prompt, userContext });
    const promptWithFullContext = `Customize the template for the repository at ${repoPath}\n\nUser Context: ${JSON.stringify(userContext)}}.\n\n${prompt}`
    console.log('Full prompt sending to endpoint:', promptWithFullContext)
    const llmResponse = await fetch(LLM_MANIPULATION_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        repoPath,
        prompt: promptWithFullContext,
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
