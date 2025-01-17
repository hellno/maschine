export type ProjectStatus = {
  state: 'setting_up' | 'failed' | 'building' | 'ready' | 'error';
  message: string;
  error?: string;
};

export function getProjectStatus(project: Project): ProjectStatus {
  // Find setup job
  const setupJob = project.jobs?.find(job => job.type === 'setup_project');
  
  if (!setupJob) {
    return {
      state: 'error',
      message: 'Project setup information not found',
    };
  }

  // Check setup job status
  if (setupJob.status === 'pending') {
    return {
      state: 'setting_up',
      message: 'Setting up your project...',
    };
  }

  if (setupJob.status === 'failed') {
    return {
      state: 'failed',
      message: 'Project setup failed',
      error: setupJob.data?.error || 'Unknown error occurred',
    };
  }

  // If setup is complete, check Vercel build status
  if (setupJob.status === 'completed') {
    const vercelStatus = project.vercel_project_id ? 'READY' : 'PENDING';
    
    switch (vercelStatus) {
      case 'PENDING':
      case 'BUILDING':
      case 'INITIALIZING':
        return {
          state: 'building',
          message: 'Building your project...',
        };
      case 'ERROR':
        return {
          state: 'error',
          message: 'Build failed',
          error: 'Vercel build failed. Please check the logs for details.',
        };
      case 'READY':
        return {
          state: 'ready',
          message: 'Your project is ready!',
        };
      default:
        return {
          state: 'error',
          message: 'Unknown project state',
        };
    }
  }

  return {
    state: 'error',
    message: 'Unknown project state',
  };
}
