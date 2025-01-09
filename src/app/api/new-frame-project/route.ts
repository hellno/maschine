import { NextResponse } from "next/server";
import { Octokit } from "octokit";
import crypto from "crypto";
import { setTimeout } from 'timers/promises';

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
    // Get the contents of the current directory
    const { data: contents } = await octokit.rest.repos.getContent({
      owner: sourceOwner,
      repo: sourceRepo,
      path,
    });

    if (Array.isArray(contents)) {
      for (const item of contents) {
        if (item.type === "file") {
          // Get the file content
          const { data: fileContent } = await octokit.rest.repos.getContent({
            owner: sourceOwner,
            repo: sourceRepo,
            path: item.path,
          });

          // Use the raw base64 content directly
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const content = (fileContent as any).content;

          // Create the file in the new repository
          await octokit.rest.repos.createOrUpdateFileContents({
            owner: targetOwner,
            repo: targetRepo,
            path: item.path,
            message: `Initial commit: Copy ${item.path} from ${sourceRepo}`,
            content, // Use the raw base64 content
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
      }
    }
  } catch (error) {
    console.error(`Error copying contents from ${path}:`, error);
    throw error;
  }
};

export async function POST(request: Request) {
  try {
    // Simulate processing delay
    await setTimeout(2000);

    // Parse the request body
    const body = await request.json();
    const { prompt, description } = body;

    // Validate input
    if (!prompt || !description) {
      return NextResponse.json(
        { error: "Project name and description are required" },
        { status: 400 }
      );
    }

    // AI! add an API call to deepseek api to summarize the prompt into a simple github repo name
    // force it to only respond with the project name, nothing else, no chatting, no description
    // docs at: https://api-docs.deepseek.com/
    const projectName = prompt;

    // Sanitize the project name for Vercel
    const sanitizedProjectName = sanitizeProjectName(prompt);

    // Authenticate with GitHub
    const octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN,
    });

    console.log("Creating new repository with data", { prompt, description });

    // Step 1: Create a new empty repository
    const createRepoResponse = await octokit.rest.repos.createInOrg({
      org: "frameception",
      name: sanitizedProjectName,
      description,
      private: false,
    });

    const newRepoUrl = createRepoResponse.data.html_url;
    const newRepoOwner = 'frameception'; // createRepoResponse.data.owner.login;
    const newRepoName = createRepoResponse.data.name;

    console.log("Created new repository:", newRepoName, 'data: ', createRepoResponse.data);

    // Step 2: Copy the entire contents of the frames-v2-demo repository
    await copyRepositoryContents(
      octokit,
      "hellno",
      "farcaster-frames-template",
      newRepoOwner,
      newRepoName
    );

    console.log("Copied all contents to new repository");

    // Step 3: Create a Vercel project linked to the new repository
    const vercelResponse = await fetch("https://api.vercel.com/v9/projects", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.VERCEL_TOKEN}`,
      },
      body: JSON.stringify({
        name: sanitizedProjectName, // Use the sanitized project name for Vercel
        gitRepository: {
          type: "github",
          repo: `${newRepoOwner}/${newRepoName}`,
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
    console.log("Created Vercel project:", vercelProject);

    // Step 4: Trigger a deployment using the repoId
    const deployment = await triggerVercelDeployment(
      sanitizedProjectName,
      vercelProject.link.repoId // Use the repoId from the Vercel project creation response
    );

    // Return the created project, repository URL, and Vercel deployment URL
    const newProject = {
      prompt,
      description,
      repoUrl: newRepoUrl,
      vercelUrl: deployment.url,
      createdAt: new Date().toISOString(),
    };

    return NextResponse.json(newProject, { status: 201 });
  } catch (error) {
    console.error("Error creating new frame project:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
