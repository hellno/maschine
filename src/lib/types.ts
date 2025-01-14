/* eslint-disable @typescript-eslint/no-explicit-any */
import { FrameContext } from "@farcaster/frame-sdk"

export interface TemplateCustomizationRequest {
  prompt: string
  userContext: FrameContext
}

export interface TemplateCustomizationResponse {
  success: boolean
  result?: string
  error?: string
}

export interface Project {
  id: string;
  created_at: string;
  repo_url: string;
  frontend_url: string;
  fid_owner: number;
  jobs?: Job[];
  logs?: Log[];
}
export interface Job {
  id: string;
  status: "pending" | "completed" | "failed";
  created_at: string;
  data: any;
}

export interface Log {
  id: string;
  created_at: string;
  source: string;
  text: string;
}

