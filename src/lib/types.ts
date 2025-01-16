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
  name: string;
  created_at: string;
  repo_url: string;
  frontend_url: string;
  fid_owner: number;
  vercel_project_id?: string;
  jobs?: Job[];
}

export interface Job {
  id: string;
  type: string;
  status: "pending" | "completed" | "failed";
  created_at: string;
  data: any;
  logs?: Log[];
}

interface VercelLogPayload {
  deploymentId: string;
  info?: {
    type: string;
    name: string;
    entrypoint: string;
  };
  text: string;
  id: string;
  date: number;
  serial: string;
}

export interface VercelLogData {
  source: 'vercel';
  text: string;
  type: 'stdout' | 'stderr';
  payload: VercelLogPayload;
}

export interface Log {
  id: string;
  created_at: string;
  source: string;
  text: string;
  data?: {
    logs?: VercelLogData[];
    [key: string]: any;
  };
}

