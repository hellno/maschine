import { NextResponse, NextRequest } from "next/server";

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
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

async function initRepoIfEmpty(
  octokit: Octokit,
  owner: string,
  repo: string,
  branch = "main",
  verbose: boolean = true
) {
  try {
    if (verbose) {
      console.log('Checking if repository is empty...');
    }
    await octokit.rest.repos.getCommit({
      owner,
      repo,
      ref: `heads/${branch}`,
    });
    if (verbose) {
      console.log('Repository is not empty');
    }
  } catch (err: any) {
    if (err.status === 409) {
      if (verbose) {
        console.log('Repository is empty, creating initial README...');
      }
      await octokit.rest.repos.createOrUpdateFileContents({
        owner,
        repo,
        path: "README.md",
        message: "Initial commit: Add README",
        content: Buffer.from(`# Readme`).toString("base64"),
      });
      if (verbose) {
        console.log('Repository initialized with README');
      }
    } else {
      if (verbose) {
        console.error('Error checking repository status:', err);
      }
      throw err;
    }
  }
}

const commitCollectedFiles = async (
  octokit: Octokit,
  targetOwner: string,
  targetRepo: string,
  files: FileChange[],
  commitMessage: string,
  verbose: boolean = true
) => {
  try {
    if (verbose) {
      console.log('Starting commit process...');
    }

    const { data: repoData } = await octokit.rest.repos.get({
      owner: targetOwner,
      repo: targetRepo,
    });
    const defaultBranch = repoData.default_branch;

    if (verbose) {
      console.log(`Working with default branch: ${defaultBranch}`);
    }

    // Initialize repository if empty
    if (verbose) {
      console.log('Checking if repository is empty...');
    }
    await initRepoIfEmpty(octokit, targetOwner, targetRepo);

    // Get the latest commit to find the tree SHA
    if (verbose) {
      console.log('Getting latest commit...');
    }
    const commitResponse = await octokit.rest.repos.getCommit({
      owner: targetOwner,
      repo: targetRepo,
      ref: `heads/${defaultBranch}`,
    });

    const baseTreeSha = commitResponse.data.commit.tree.sha;
    const parentCommits = [commitResponse.data.sha];

    if (verbose) {
      console.log('Latest commit found:', commitResponse.data);
    }

    // Create blobs for all files
    if (verbose) {
      console.log('Creating blobs...');
    }

    const blobPromises = files.map((file) =>
      octokit.rest.git.createBlob({
        owner: targetOwner,
        repo: targetRepo,
        content: file.content, // Use the base64 content directly
        encoding: "base64",    // Specify base64 encoding
      })
    );

    if (verbose) {
      console.log('All blob promises created');
    }
    const blobs = await Promise.all(blobPromises);

    if (verbose) {
      console.log('All blobs created successfully');
    }

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
    if (verbose) {
      console.error('Detailed error during commit:', {
        error: error instanceof Error ? error.message : error,
        stack: error instanceof Error ? error.stack : undefined,
        status: error.status,
        response: error.response?.data,
        request: error.request
      });
    }
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
      `https://api.vercel.com/v13/deployments?teamId=${process.env.VERCEL_TEAM_ID}`,
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
  path: string = "",
  verbose: boolean = false
) => {
  try {
    if (verbose) {
      console.log('Starting to collect repository contents...');
    }

    const files = await collectRepositoryContents(
      octokit,
      sourceOwner,
      sourceRepo,
      path
    );

    if (verbose) {
      console.log(`Collected ${files.length} files from source repository`);
    }

    if (files.length === 0) {
      if (verbose) {
        console.log("No files to copy.");
      }
      console.log("No files to copy.");
      return;
    }

    const commitMessage = `Copy template from ${sourceRepo}`;
    if (verbose) {
      console.log('Starting to commit collected files...');
    }

    await commitCollectedFiles(octokit, targetOwner, targetRepo, files, commitMessage);

    if (verbose) {
      console.log('Files committed successfully');
    }
  } catch (error) {
    if (verbose) {
      console.error('Detailed error during repository copy:', {
        error: error instanceof Error ? error.message : error,
        stack: error instanceof Error ? error.stack : undefined,
        status: error.status,
        response: error.response?.data,
        request: error.request
      });
    }
    console.error("Error copying repository contents:", error);
    throw error;
  }
};

export async function POST(req: NextRequest) {
  console.log('Received new-frame-project request:', req);
  const encoder = new TextEncoder();

  // Create a readable stream
  const stream = new ReadableStream({
    async start(controller) {
      // Helper to send updates
      function sendStatusUpdate(msg: string) {
        console.log('Status Update', msg)
        controller.enqueue(encoder.encode(msg + '\n'));
      }

      try {
        // 1. Parse input
        sendStatusUpdate('Parsing request...');
        const body = await req.json();
        const { prompt, description, username, verbose = false } = body;

        if (!prompt || !description) {
          sendStatusUpdate('Error: Project name and description are required');
          controller.close();
          return;
        }

        // Create Octokit instance
        const octokit = new Octokit({
          auth: process.env.GITHUB_TOKEN,
        });

        // 2. Generate project name
        sendStatusUpdate('Generating project name...');
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
        const sanitizedProjectName = `${username ? `${username}-` : ''}${sanitizeProjectName(projectName)}`;
        sendStatusUpdate(`Project name: ${sanitizedProjectName}`);

        // 3. Create GitHub repository
        sendStatusUpdate('Creating GitHub repository...');
        const createRepoResponse = await octokit.rest.repos.createInOrg({
          org: "frameception-v2",
          name: sanitizedProjectName,
          description: username
            ? `${description} (created by @${username})`
            : description,
          private: false,
        });
        sendStatusUpdate('Repository created successfully');

        // 4. Copy template files
        sendStatusUpdate('Copying template files...');
        await copyRepositoryContents(
          octokit,
          "hellno",
          "farcaster-frames-template",
          "frameception-v2",
          sanitizedProjectName,
          "",
          verbose
        );
        sendStatusUpdate('Template files copied successfully');

        // 5. Create Vercel project
        sendStatusUpdate('Creating Vercel project...');
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
          throw new Error("Failed to create Vercel project");
        }
        sendStatusUpdate('Vercel project created successfully');

        // 6. Trigger deployment
        sendStatusUpdate('Triggering deployment...');
        const vercelProject = await vercelResponse.json();
        const deployment = await triggerVercelDeployment(
          sanitizedProjectName,
          vercelProject.link.repoId
        );
        sendStatusUpdate('Deployment triggered successfully');

        // Final success message
        sendStatusUpdate('Project creation complete!');
        sendStatusUpdate(`Repository: ${createRepoResponse.data.html_url}`);
        sendStatusUpdate(`Vercel URL: ${deployment.url}`);

      } catch (error) {
        // Send error status
        controller.enqueue(encoder.encode(`Error: ${error instanceof Error ? error.message : 'Unknown error'}\n`));
      } finally {
        controller.close();
      }
    },
  });

  // Return the stream as the response
  return new Response(stream, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
