import { Project } from "../types";

// aggregation of project status across different services: our backend and vercel
export type ProjectStatus = {
  state: 'created' | 'deploying' | 'deployed' | 'failed' | 'error' | 'unknown';
  message: string;
  error?: string;
};

export enum VercelBuildStatus {
  READY = 'READY',
  BUILDING = 'BUILDING',
  INITIALIZING = 'INITIALIZING',
  ERROR = 'ERROR',
  QUEUED = 'QUEUED',
}

export function getMergedProjectStatus(project: Project | null, vercelStatus: VercelBuildStatus | null): ProjectStatus {
  if (!project) {
    return { state: 'error', message: 'Project not found' };
  }

  // First handle raw DB states
  switch (project.status) {
    case 'created':
      return { state: 'created', message: 'Project created - awaiting deployment' };
    case 'deploying':
      return { state: 'deploying', message: 'Deploying to Vercel' };
    case 'failed':
      return {
        state: 'failed',
        message: 'Deployment failed',
        error: 'Unknown error occurred'
      };
    case 'error':
      return {
        state: 'error',
        message: 'Project error',
        error: 'Unknown error'
      };
    case 'unknown':
      return { state: 'unknown', message: 'Unknown project state' };
  }

  // Then handle deploying state with Vercel status
  if (project.status === 'deployed') {
    switch (vercelStatus) {
      case null:
        return { state: 'deploying', message: 'Starting deployment...' };
      case 'QUEUED':
        return { state: 'deploying', message: 'Deployment queued' };
      case 'BUILDING':
        return { state: 'deploying', message: 'Building...' };
      case 'INITIALIZING':
        return { state: 'deploying', message: 'Initializing...' };
      case 'ERROR':
        return {
          state: 'error',
          message: 'Build error',
          error: 'Vercel build failed. Check logs for details.'
        };
      case 'READY':
        return { state: 'deployed', message: 'Successfully deployed' };
      default:
        return { state: 'unknown', message: 'Unknown deployment state' };
    }
  }

  return { state: 'unknown', message: 'Unknown project state' };
}
