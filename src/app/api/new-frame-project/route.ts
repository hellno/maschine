import { NextResponse } from "next/server";
import { Octokit } from "octokit";
import crypto from "crypto";
import { setTimeout } from 'timers/promises';
import { OpenAI } from "openai";

// Cache for repository metadata to reduce API calls
const repoMetadataCache = new Map();

const getRepoMetadata = async (octokit: Octokit, owner: string, repo: string) => {
  const cacheKey = `${owner}/${repo}`;
  
  if (repoMetadataCache.has(cacheKey)) {
    return repoMetadataCache.get(cacheKey);
  }

  const { data } = await octokit.rest.repos.get({
    owner,
    repo,
  });

  repoMetadataCache.set(cacheKey, data);
  return data;
};

const deepseek = new OpenAI({
  apiKey: process.env.DEEPSEEK_API_KEY,
  baseURL: "https://api.deepseek.com",
});

// Helper function to trigger a Vercel deployment
const triggerVercelDeployment = async (projectName: string, repoId: number) => {
  try {
    const response = await fetch(
      `https://api.vercel.com/v13/deployments`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${process.env.VERCEL_TOKEN}`,
        },
        body: JSON.stringify({
          name: projectName,
          gitSource: {
            type: "github",
            repoId: repoId,
            ref: "main",
          },
        }),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      console.error("Failed to trigger deployment:", error);
      throw new Error("Failed to trigger deployment");
    }

    const deployment = await response.json();
    console.log("Deployment triggered successfully:", deployment);
    return deployment;
  } catch (error) {
    console.error("Error triggering deployment:", error);
    throw error;
  }
};

// Helper function to generate a random NEXTAUTH_SECRET
const generateRandomSecret = () => {
  const randomBytes = crypto.getRandomValues(new Uint8Array(32));
  return Buffer.from(randomBytes).toString('base64');
};

// Helper function to sanitize project names for Vercel
const sanitizeProjectName = (name: string): string => {
  // Convert to lowercase
  let sanitized = name.toLowerCase();

  // Replace invalid characters with '-'
  sanitized = sanitized.replace(/[^a-z0-9._-]/g, '-');

  // Remove sequences of '---' or more
  sanitized = sanitized.replace(/---+/g, '-');

  // Trim to 100 characters
  sanitized = sanitized.substring(0, 100);

  // Ensure the name doesn't start or end with a hyphen
  sanitized = sanitized.replace(/^-+|-+$/g, '');

  // If the name is empty after sanitization, use a default
  if (!sanitized) {
    sanitized = 'new-frame-project';
  }

  return sanitized;
};

// Helper function to recursively copy repository contents
const copyRepositoryContents = async (
  octokit: Octokit,
  sourceOwner: string,
  sourceRepo: string,
  targetOwner: string,
  targetRepo: string,
  path: string = ""
) => {
  console.log(`Copying contents from ${path} in ${sourceRepo} to ${targetRepo}`);
  
  try {
    // Get contents of current directory
    const { data: contents } = await octokit.rest.repos.getContent({
      owner: sourceOwner,
      repo: sourceRepo,
      path,
    });

    if (Array.isArray(contents)) {
      // Process files and directories in parallel
      await Promise.all(contents.map(async (item) => {
        if (item.type === "file") {
          // Get file content
          const { data: fileContent } = await octokit.rest.repos.getContent({
            owner: sourceOwner,
            repo: sourceRepo,
            path: item.path,
          });

          // Create file in new repository
          await octokit.rest.repos.createOrUpdateFileContents({
            owner: targetOwner,
            repo: targetRepo,
            path: item.path,
            message: `Initial commit: Copy ${item.path} from ${sourceRepo}`,
            content: (fileContent as any).content,
          });

          console.log(`Copied file: ${item.path}`);
        } else if (item.type === "dir") {
          // Recursively copy directories
          await copyRepositoryContents(
            octokit,
            sourceOwner,
            sourceRepo,
            targetOwner,
            targetRepo,
            item.path
          );
        }
      }));
    }
  } catch (error) {
    console.error(`Error copying contents from ${path}:`, error);
    throw error;
  }
};

export async function POST(request: Request) {
  try {
    // Parse request and validate input
    const body = await request.json();
    const { prompt, description, username } = body;

    if (!prompt || !description) {
      return NextResponse.json(
        { error: "Project name and description are required" },
        { status: 400 }
      );
    }

    // Create Octokit instance
    const octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN,
    });

    // Generate project name and get template repo data in parallel
    const [projectNameResponse, templateRepoData] = await Promise.all([
      deepseek.chat.completions.create({
        model: "deepseek-chat",
        messages: [
          {
            role: "system",
            content: "You are a helpful assistant that generates concise, technical project names. Only respond with the project name, nothing else. No descriptions, no explanations, no additional text. Just the name.",
          },
          {
            role: "user",
            content: `Generate a short, technical project name based on this description: ${prompt}`,
          },
        ],
        temperature: 0.7,
        max_tokens: 20,
      }),
      getRepoMetadata(octokit, "hellno", "farcaster-frames-template")
    ]);

    const projectName = projectNameResponse.choices[0].message.content.trim();
    const sanitizedProjectName = `${username ? `${username}-` : ''}${sanitizeProjectName(projectName)}`;

    // Create repository and copy contents in parallel
    const [createRepoResponse] = await Promise.all([
      octokit.rest.repos.createInOrg({
        org: "frameception",
        name: sanitizedProjectName,
        description: username 
          ? `${description} (created by @${username})`
          : description,
        private: false,
      }),
      copyRepositoryContents(
        octokit,
        "hellno",
        "farcaster-frames-template",
        "frameception",
        sanitizedProjectName
      )
    ]);

    // Create Vercel project
    const vercelResponse = await fetch("https://api.vercel.com/v9/projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.VERCEL_TOKEN}`,
      },
      body: JSON.stringify({
        name: sanitizedProjectName,
        gitRepository: {
          type: "github",
          repo: `frameception/${sanitizedProjectName}`,
        },
        framework: "nextjs",
        installCommand: "yarn install",
        buildCommand: "yarn build",
        outputDirectory: ".next",
        environmentVariables: [
          {
            "key": "NEXTAUTH_SECRET",
            "target": "production",
            "type": "sensitive",
            "value": generateRandomSecret()
          },
          {
            "key": "KV_REST_API_URL",
            "target": "production",
            "type": "sensitive",
            "value": process.env.KV_REST_API_URL
          },
          {
            "key": "KV_REST_API_TOKEN",
            "target": "production",
            "type": "sensitive",
            "value": process.env.KV_REST_API_TOKEN
          }
        ],
      }),
    });

    if (!vercelResponse.ok) {
      const vercelError = await vercelResponse.json();
      console.error("Vercel project creation failed:", vercelError);
      throw new Error("Failed to create Vercel project");
    }

    const vercelProject = await vercelResponse.json();

    // Trigger deployment
    const deployment = await triggerVercelDeployment(
      sanitizedProjectName,
      vercelProject.link.repoId
    );

    return NextResponse.json({
      prompt,
      description,
      repoUrl: createRepoResponse.data.html_url,
      vercelUrl: deployment.url,
      createdAt: new Date().toISOString(),
    }, { status: 201 });
  } catch (error) {
    console.error("Error creating new frame project:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
