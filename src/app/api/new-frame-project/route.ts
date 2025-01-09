import { NextResponse } from "next/server";
import { Octokit } from "octokit";
import crypto from "crypto";
import { setTimeout } from 'timers/promises';
import { OpenAI } from "openai";

interface FileChange {
  path: string;
  content: string;
}

// Cache for repository metadata to reduce API calls
const repoMetadataCache = new Map();

const collectRepositoryContents = async (
  octokit: Octokit,
  sourceOwner: string,
  sourceRepo: string,
  path: string = "",
  fileList: FileChange[] = []
): Promise<FileChange[]> => {
  console.log(`Collecting contents from ${path} in ${sourceRepo}`);
  try {
    const { data: contents } = await octokit.rest.repos.getContent({
      owner: sourceOwner,
      repo: sourceRepo,
      path,
    });

    if (Array.isArray(contents)) {
      for (const item of contents) {
        if (item.type === "file") {
          const { data: fileContent } = await octokit.rest.repos.getContent({
            owner: sourceOwner,
            repo: sourceRepo,
            path: item.path,
          });

          fileList.push({
            path: item.path,
            content: (fileContent as any).content,
          });
          // console.log(`Queued file: ${item.path}`);
        } else if (item.type === "dir") {
          await collectRepositoryContents(
            octokit,
            sourceOwner,
            sourceRepo,
            item.path,
            fileList
          );
        }
      }
    }

    return fileList;
  } catch (error) {
    console.error(`Error collecting contents from ${path}:`, error);
    throw error;
  }
};

const commitCollectedFiles = async (
  octokit: Octokit,
  targetOwner: string,
  targetRepo: string,
  files: FileChange[],
  commitMessage: string
) => {
  try {
    const { data: repoData } = await octokit.rest.repos.get({
      owner: targetOwner,
      repo: targetRepo,
    });
    const defaultBranch = repoData.default_branch;

    let baseTreeSha: string | undefined;
    let parentCommits: string[] = [];

    try {
      // Get the latest commit to find the tree SHA
      const commitResponse = await octokit.rest.repos.getCommit({
        owner: targetOwner,
        repo: targetRepo,
        ref: `heads/${defaultBranch}`,
      });
      baseTreeSha = commitResponse.data.commit.tree.sha;
      parentCommits = [commitResponse.data.sha];
    } catch (error) {
      // If the repository is empty (409 Conflict), create initial empty commit
      if (error.status === 409) {
        const { data: emptyTree } = await octokit.rest.git.createTree({
          owner: targetOwner,
          repo: targetRepo,
          tree: [],
        });

        const { data: emptyCommit } = await octokit.rest.git.createCommit({
          owner: targetOwner,
          repo: targetRepo,
          message: "Initial empty commit",
          tree: emptyTree.sha,
          parents: [],
        });

        await octokit.rest.git.updateRef({
          owner: targetOwner,
          repo: targetRepo,
          ref: `heads/${defaultBranch}`,
          sha: emptyCommit.sha,
          force: true,
        });

        baseTreeSha = emptyTree.sha;
        parentCommits = [emptyCommit.sha];
      } else {
        throw error;
      }
    }

    console.log('baseTreeSha', baseTreeSha, 'parentCommits', parentCommits);

    // Create blobs for all files
    const blobPromises = files.map((file) =>
      octokit.rest.git.createBlob({
        owner: targetOwner,
        repo: targetRepo,
        content: file.content, // Use the base64 content directly
        encoding: "base64",    // Specify base64 encoding
      })
    );

    console.log('create all blob promises')
    const blobs = await Promise.all(blobPromises);
    console.log('awaited all blobs');

    const treeElements = files.map((file, index) => ({
      path: file.path,
      mode: "100644",
      type: "blob",
      sha: blobs[index].data.sha,
    }));

    console.log('Create initial tree');
    // Create initial tree
    const { data: newTree } = await octokit.rest.git.createTree({
      owner: targetOwner,
      repo: targetRepo,
      tree: treeElements,
      base_tree: baseTreeSha, // Will be undefined for empty repos
    });

    console.log('created new tree');
    // Create initial commit
    const { data: newCommit } = await octokit.rest.git.createCommit({
      owner: targetOwner,
      repo: targetRepo,
      message: commitMessage,
      tree: newTree.sha,
      parents: parentCommits, // Will be empty array for empty repos
    });

    console.log('created new commit');
    // Update reference
    await octokit.rest.git.updateRef({
      owner: targetOwner,
      repo: targetRepo,
      ref: `heads/${defaultBranch}`,
      sha: newCommit.sha,
    });

    console.log(`Successfully committed ${files.length} files.`);
  } catch (error) {
    console.error("Error committing files:", error);
    throw error;
  }
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

// Helper function to copy repository contents using bulk commit
const copyRepositoryContents = async (
  octokit: Octokit,
  sourceOwner: string,
  sourceRepo: string,
  targetOwner: string,
  targetRepo: string,
  path: string = ""
) => {
  try {
    const files = await collectRepositoryContents(
      octokit,
      sourceOwner,
      sourceRepo,
      path
    );

    if (files.length === 0) {
      console.log("No files to copy.");
      return;
    }

    const commitMessage = `Initial bulk commit: Copy contents from ${sourceRepo}`;
    await commitCollectedFiles(octokit, targetOwner, targetRepo, files, commitMessage);
  } catch (error) {
    console.error("Error copying repository contents:", error);
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
    const [projectNameResponse] = await Promise.all([
      deepseek.chat.completions.create({
        model: "deepseek-chat",
        messages: [
          {
            role: "system",
            content: "You are a helpful assistant that generates concise, aspirational project names. Only respond with the project name, nothing else. No descriptions, no explanations, no additional text. Just the name.",
          },
          {
            role: "user",
            content: `Generate a short, aspirational project name based on this description: ${prompt}`,
          },
        ],
        temperature: 1.5,
        max_tokens: 20,
      }),
    ]);

    const projectName = projectNameResponse.choices[0].message.content.trim();

    if (!projectName) {
      return NextResponse.json(
        { error: "Failed to generate project name" },
        { status: 500 }
      );
    }

    const sanitizedProjectName = `${username ? `${username}-` : ''}${sanitizeProjectName(projectName)}`;

    // Create repository first
    const createRepoResponse = await octokit.rest.repos.createInOrg({
      org: "frameception-v2",
      name: sanitizedProjectName,
      description: username
        ? `${description} (created by @${username})`
        : description,
      private: false,
    });

    // Wait a moment to ensure repository is fully initialized
    await setTimeout(1000);

    // Then copy contents
    await copyRepositoryContents(
      octokit,
      "hellno",
      "farcaster-frames-template",
      "frameception-v2",
      sanitizedProjectName
    );

    // Create Vercel project
    const vercelResponse = await fetch(`https://api.vercel.com/v9/projects?teamId=${process.env.VERCEL_TEAM_ID}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.VERCEL_TOKEN}`,
      },
      body: JSON.stringify({
        name: sanitizedProjectName,
        gitRepository: {
          type: "github",
          repo: `frameception-v2/${sanitizedProjectName}`,
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
    
    // Handle specific GitHub repository name conflict
    if (error instanceof Error && error.message.includes("name already exists on this account")) {
      return NextResponse.json(
        { error: "A project with this name already exists. Please try a different name." },
        { status: 409 }
      );
    }

    // Handle other GitHub API errors
    if (error.status === 422) {
      return NextResponse.json(
        { error: "Invalid project name. Please try a different name." },
        { status: 400 }
      );
    }

    // Generic error fallback
    return NextResponse.json(
      { error: "An unexpected error occurred while creating your project. Please try again." },
      { status: 500 }
    );
  }
}
