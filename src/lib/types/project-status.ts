import { Project } from "../types";

// aggregation of project status across different services: our backend and vercel
export type ProjectStatus = {
  state: 'setting_up' | 'failed' | 'building' | 'ready' | 'error' | 'unknown';
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

export function getProjectStatus(project: Project | null, vercelStatus: VercelBuildStatus | null): ProjectStatus {
  if (!project) {
    return {
      state: 'error',
      message: 'Project not found',
    };
  }

  const setupJob = project.jobs?.find(job => job.type === 'setup_project');

  if (!setupJob) {
    return {
      state: 'error',
      message: 'Info not found',
    };
  }

  // Check setup job status
  if (setupJob.status === 'pending') {
    return {
      state: 'setting_up',
      message: 'Setting up frame...',
    };
  }

  if (setupJob.status === 'failed') {
    return {
      state: 'failed',
      message: 'Setup failed',
      error: setupJob.data?.error || 'Unknown error occurred',
    };
  }

  // If setup is complete, check Vercel build status
  if (setupJob.status === 'completed') {
    switch (vercelStatus) {
      case null:
        return {
          state: 'unknown',
          message: '',
        };
      case 'QUEUED':
      case 'BUILDING':
      case 'INITIALIZING':
        return {
          state: 'building',
          message: 'Building',
        };
      case 'ERROR':
        return {
          state: 'error',
          message: 'Build error',
          error: 'Vercel build failed. Please check the logs for details.',
        };
      case 'READY':
        return {
          state: 'ready',
          message: 'Ready',
        };
      default:
        return {
          state: 'error',
          message: 'Unknown state',
        };
    }
  }

  return {
    state: 'error',
    message: 'Unknown project state',
  };
}
