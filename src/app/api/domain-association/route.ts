import { NextResponse } from "next/server";
import { ethers } from "ethers";

const FID = process.env.FID ? parseInt(process.env.FID) : 0;
const CUSTODY_ADDRESS = process.env.CUSTODY_ADDRESS || '';
const PRIVATE_KEY = process.env.PRIVATE_KEY || '';

export async function POST(request: Request) {
  try {
    // Parse request body
    const { domain } = await request.json();

    if (!domain) {
      return NextResponse.json(
        { error: "Domain is required" },
        { status: 400 }
      );
    }

    // Validate environment variables
    if (!FID || !CUSTODY_ADDRESS || !PRIVATE_KEY) {
      return NextResponse.json(
        { error: "Server configuration incomplete" },
        { status: 500 }
      );
    }

    // Create header and payload
    const header = { 
      fid: FID, 
      type: 'custody', 
      key: CUSTODY_ADDRESS 
    };
    
    const payload = { 
      domain: domain 
    };

    // Encode components
    const encodedHeader = Buffer.from(JSON.stringify(header), 'utf-8').toString('base64url');
    const encodedPayload = Buffer.from(JSON.stringify(payload), 'utf-8').toString('base64url');

    // Create wallet and sign message
    const wallet = new ethers.Wallet(PRIVATE_KEY);
    const message = `${encodedHeader}.${encodedPayload}`;
    const signature = await wallet.signMessage(message);
    const encodedSignature = Buffer.from(signature, 'utf-8').toString('base64url');

    // Create response formats
    const compactJfs = `${encodedHeader}.${encodedPayload}.${encodedSignature}`;
    const jsonJfs = {
      header: encodedHeader,
      payload: encodedPayload,
      signature: encodedSignature
    };

    return NextResponse.json({
      compact: compactJfs,
      json: jsonJfs
    }, { status: 200 });

  } catch (error) {
    console.error("Error generating domain association:", error);
    return NextResponse.json(
      { error: "Failed to generate domain association" },
      { status: 500 }
    );
  }
}
