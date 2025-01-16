import { NextResponse } from 'next/server'

const UPDATE_CODE_ENDPOINT = 'https://herocast--update-code.modal.run';

export async function POST(request: Request) {
  try {
    const { projectId, prompt, userContext } = await request.json()
    console.log('/update-code', { projectId, prompt, userContext })
    if (!projectId || !prompt || !userContext) {
      return NextResponse.json(
        { error: 'Repo, prompt and user context are required' },
        { status: 400 }
      )
    }

    const llmResponse = await fetch(UPDATE_CODE_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        project_id: projectId,
        prompt,
        user_context: userContext,
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
