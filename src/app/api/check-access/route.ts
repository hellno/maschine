import { NextResponse } from 'next/server';

interface Requirement {
  idx: number;
  isValid: boolean;
  name: string;
  message?: string;
}
const OPENRANK_PERCENTILE_THRESHOLD = 90; // 90th percentile threshold

export async function POST(request: Request) {
  try {
    const { fids } = await request.json();

    if (!fids || !Array.isArray(fids)) {
      return NextResponse.json({ error: 'Missing FIDs in request body' }, { status: 400 });
    }

    const requirements: Requirement[] = [];

    // Requirement 1: Farcaster Account
    const hasFid = fids.length > 0;
    requirements.push({
      idx: 0,
      isValid: hasFid,
      name: 'Farcaster Account',
      message: hasFid ? 'Valid Farcaster account detected' : 'No Farcaster account found',
    });

    if (!hasFid) {
      return NextResponse.json({
        requirements,
        actionMessage: "register_farcaster_account"
      });
    }

    // Requirement 2: Top 10% Engagement
    const response = await fetch('https://graph.cast.k3l.io/scores/global/engagement/fids', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(fids),
    });

    if (!response.ok) {
      throw new Error(`Cast API request failed with status ${response.status}`);
    }

    const data = await response.json();
    const userScore = data.result.find((result: {
      fid: number
      username: string,
      rank: number,
      score: number,
      percentile: number
    }) => fids.includes(result.fid));

    requirements.push({
      idx: 1,
      isValid: userScore?.percentile > OPENRANK_PERCENTILE_THRESHOLD || false,
      name: 'Top 10% Engagement',
      message: `Your percentile: ${userScore?.percentile || 0}% based on OpenRank score`,
    });

    // Requirement 3: NFT Holder (Placeholder)
    requirements.push({
      idx: 2,
      isValid: false, // Placeholder - not implemented yet
      name: 'NFT Holder',
      message: 'NFT check not yet implemented',
    });

    // first one and either of the other two has to be Valid
    const hasAccess = requirements[0].isValid && (requirements[1].isValid || requirements[2].isValid);
    return NextResponse.json({
      requirements,
      hasAccess,
      ...(!hasAccess && {
        actionMessage: requirements[0].isValid ? "mint_nft" : "register_farcaster_account"
      })
    });
  } catch (error) {
    console.error('Access check failed:', error);
    return NextResponse.json({
      requirements: [
        {
          idx: 0,
          isValid: false,
          name: 'Farcaster Account',
          message: 'Error validating account status'
        }
      ],
      hasAccess: false,
      actionMessage: "register_farcaster_account"
    });
  }
}
