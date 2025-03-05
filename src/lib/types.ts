/* eslint-disable @typescript-eslint/no-explicit-any */
import { z } from "zod";

export interface TemplateCustomizationRequest {
  prompt: string;
  userContext: FrameContext;
}

export interface TemplateCustomizationResponse {
  success: boolean;
  result?: string;
  error?: string;
}

export interface Project {
  id: string;
  name: string;
  status: "created" | "pending" | "deploy_failed" | "error" | "deployed";
  created_at: string;
  repo_url: string;
  frontend_url: string;
  fid_owner: number;
  vercel_project_id?: string;
  jobs?: Job[];
  builds?: Build[];
  latestBuild?: Build;
  latestJob?: Job;
  hasAnyJobsPending: boolean;
}

export interface Job {
  id: string;
  type: string;
  status: "pending" | "completed" | "failed" | "running";
  created_at: string;
  data: any;
  logs?: Log[];
}

export interface Build {
  id: string;
  created_at: string;
  finished_at: string;
  status: "submitted" | "building" | "success" | "error" | "queued";
  project_id: string;
  commit_hash: string;
  vercel_build_id?: string;
  data: {
    meta?: {
      githubCommitMessage?: string;
    };
    [key: string]: any;
  };
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
  source: "vercel";
  text: string;
  type: "stdout" | "stderr";
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

// --- copied from frames sdk which cannot be imported for some reason

type AccountLocation = {
  placeId: string;
  /**
   * Human-readable string describing the location
   */
  description: string;
};
export type UserContext = {
  fid: number;
  username?: string;
  displayName?: string;
  /**
   * Profile image URL
   */
  pfpUrl?: string;
  location?: AccountLocation;
};

export type FrameLocationContextCastEmbed = {
  type: "cast_embed";
  cast: {
    fid: number;
    hash: string;
  };
};
export type FrameLocationContextNotification = {
  type: "notification";
  notification: {
    notificationId: string;
    title: string;
    body: string;
  };
};
export type FrameLocationContextLauncher = {
  type: "launcher";
};
export type FrameLocationContext =
  | FrameLocationContextCastEmbed
  | FrameLocationContextNotification
  | FrameLocationContextLauncher;
export type SafeAreaInsets = {
  top: number;
  bottom: number;
  left: number;
  right: number;
};
export type FrameContext = {
  user: {
    fid: number;
    username?: string;
    displayName?: string;
    /**
     * Profile image URL
     */
    pfpUrl?: string;
    location?: AccountLocation;
  };
  location?: FrameLocationContext;
  client: {
    clientFid: number;
    added: boolean;
    notificationDetails?: FrameNotificationDetails;
    safeAreaInsets?: SafeAreaInsets;
  };
};

export declare const notificationDetailsSchema: z.ZodObject<
  {
    url: z.ZodString;
    token: z.ZodString;
  },
  "strip",
  z.ZodTypeAny,
  {
    url: string;
    token: string;
  },
  {
    url: string;
    token: string;
  }
>;
export type FrameNotificationDetails = z.infer<
  typeof notificationDetailsSchema
>;

export interface SubscriptionTier {
  id: number;
  tierName: string;
  maxProjects?: number;
}

export interface UserSubscription {
  subscribedTier?: number;
  tierName: string;
  maxProjects?: number;
  isActive: boolean;
  expires_at?: string;
}

export interface NeynarSubscriptionData {
  contract_address: string;
  expires_at: string;
  tier: {
    id: string;
  };
}
