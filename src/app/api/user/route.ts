// ai! create a route that receives an fid and makes this request:
// const response = await fetch(
//   `https://api.neynar.com/v2/farcaster/user/subscribed_to?fid=${user.fid}&subscription_provider=fabric_stp`,
//   {
//     headers: {
//       "x-api-key": process.env.NEXT_PUBLIC_NEYNAR_API_KEY!,
//     },
//   },
// );
import { NextResponse } from 'next/server'
import { NextRequest } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const fid = searchParams.get('fid')
    
    if (!fid) {
      return NextResponse.json(
        { error: 'Missing fid parameter' },
        { status: 400 }
      )
    }

    if (!process.env.NEYNAR_API_KEY) {
      return NextResponse.json(
        { error: 'Neynar API key not configured' },
        { status: 500 }
      )
    }

    const response = await fetch(
      `https://api.neynar.com/v2/farcaster/user/subscribed_to?fid=${fid}&subscription_provider=fabric_stp`,
      {
        headers: {
          'Content-Type': 'application/json',
          'api_key': process.env.NEYNAR_API_KEY
        }
      }
    )

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch subscription status' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data.subscribed_to)

  } catch (error) {
    console.error('Error checking subscription:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
