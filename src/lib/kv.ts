import { FrameNotificationDetails } from "@farcaster/frame-sdk";
import { Redis } from "@upstash/redis";
import crypto from "crypto";

interface UserInfo {
  username?: string;
  fid: number;
  // Add other user fields as needed
}

interface ProjectInfo {
  projectId: string;
  repoUrl: string;
  vercelUrl: string;
  createdAt: number;
}

interface JobInfo {
  jobId: string;
  projectId: string;
  status: "pending" | "in-progress" | "completed" | "failed";
  createdAt: number;
  updatedAt: number;
  logs?: string[];
  error?: string;
}

function getJobKey(jobId: string): string {
  return `job:${jobId}`;
}

function getProjectJobsKey(projectId: string): string {
  return `project:${projectId}:jobs`;
}

export async function createJob(projectId: string): Promise<JobInfo> {
  const jobId = generateProjectId();
  const jobInfo: JobInfo = {
    jobId,
    projectId,
    status: "pending",
    createdAt: Date.now(),
    updatedAt: Date.now()
  };

  await redis.hset(getJobKey(jobId), jobInfo);
  await redis.sadd(getProjectJobsKey(projectId), jobId);
  
  return jobInfo;
}

export async function updateJob(jobId: string, updates: Partial<JobInfo>): Promise<void> {
  await redis.hset(getJobKey(jobId), {
    ...updates,
    updatedAt: Date.now()
  });
}

export async function getJob(jobId: string): Promise<JobInfo | null> {
  return await redis.hgetall(getJobKey(jobId)) as unknown as JobInfo;
}

export async function getProjectJobs(projectId: string): Promise<JobInfo[]> {
  const jobIds = await redis.smembers(getProjectJobsKey(projectId));
  const jobs = await Promise.all(
    jobIds.map(async (jobId) => {
      return await getJob(jobId);
    })
  );
  return jobs.sort((a, b) => b.createdAt - a.createdAt);
}

const redis = new Redis({
  url: process.env.KV_REST_API_URL,
  token: process.env.KV_REST_API_TOKEN,
});

// User-related functions
function getUserKey(fid: number): string {
  return `user:${fid}`;
}

function getUserProjectsKey(fid: number): string {
  return `user:${fid}:projects`;
}

function getProjectKey(projectId: string): string {
  return `project:${projectId}`;
}

function getUserNotificationDetailsKey(fid: number): string {
  return `user:${fid}:notifications`;
}

export async function createOrUpdateUser(fid: number, username?: string): Promise<void> {
  const userKey = getUserKey(fid);
  await redis.hset(userKey, {
    fid,
    username: username || '',
    updatedAt: Date.now()
  });
}

export async function addUserProject(fid: number, projectInfo: ProjectInfo): Promise<void> {
  const projectKey = getProjectKey(projectInfo.projectId);
  const userProjectsKey = getUserProjectsKey(fid);
  
  // Store project info
  await redis.hset(projectKey, {
    ...projectInfo,
    createdAt: Date.now()
  });
  
  // Add project to user's project set
  await redis.sadd(userProjectsKey, projectInfo.projectId);
}

export async function getUserProjects(fid: number): Promise<ProjectInfo[]> {
  const userProjectsKey = getUserProjectsKey(fid);
  const projectIds = await redis.smembers(userProjectsKey);
  
  const projects = await Promise.all(
    projectIds.map(async (projectId) => {
      const projectKey = getProjectKey(projectId);
      return await redis.hgetall(projectKey) as unknown as ProjectInfo;
    })
  );
  
  // Sort by creation date (newest first)
  return projects.sort((a, b) => b.createdAt - a.createdAt);
}

export async function deleteUserProject(fid: number, projectId: string): Promise<void> {
  const userProjectsKey = getUserProjectsKey(fid);
  const projectKey = getProjectKey(projectId);
  
  // Remove from user's project set
  await redis.srem(userProjectsKey, projectId);
  
  // Delete project data
  await redis.del(projectKey);
}

export function generateProjectId(): string {
  return crypto.randomBytes(16).toString('hex');
}

export async function getUserNotificationDetails(
  fid: number
): Promise<FrameNotificationDetails | null> {
  return await redis.get<FrameNotificationDetails>(
    getUserNotificationDetailsKey(fid)
  );
}

export async function setUserNotificationDetails(
  fid: number,
  notificationDetails: FrameNotificationDetails
): Promise<void> {
  await redis.set(getUserNotificationDetailsKey(fid), notificationDetails);
}

export async function deleteUserNotificationDetails(
  fid: number
): Promise<void> {
  await redis.del(getUserNotificationDetailsKey(fid));
}
