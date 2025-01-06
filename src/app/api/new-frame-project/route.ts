import { NextResponse } from "next/server";
import { Octokit } from "octokit";

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


export async function POST(request: Request) {
  try {
    // Parse the request body
    const body = await request.json();
    const { projectName, description } = body;

    // Validate input
    if (!projectName || !description) {
      return NextResponse.json(
        { error: "Project name and description are required" },
        { status: 400 }
      );
    }

    // Sanitize the project name for Vercel
    const sanitizedProjectName = sanitizeProjectName(projectName);

    // Authenticate with GitHub
    const octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN,
    });

    console.log("Creating new repository with data", { projectName, description });

    // Step 1: Create a new empty repository
    const createRepoResponse = await octokit.rest.repos.createForAuthenticatedUser({
      name: projectName,
      description,
      private: false, // Set to true if you want private repositories
    });

    const newRepoUrl = createRepoResponse.data.html_url;
    const newRepoOwner = createRepoResponse.data.owner.login;
    const newRepoName = createRepoResponse.data.name;

    console.log("Created new repository:", createRepoResponse.data);

    // Step 2: Get the contents of the frames-v2-demo repository
    const { data: sourceContents } = await octokit.rest.repos.getContent({
      owner: "farcasterxyz",
      repo: "frames-v2-demo",
      path: "",
    });

    // Step 3: Copy each file/folder to the new repository
    if (Array.isArray(sourceContents)) {
      for (const item of sourceContents) {
        if (item.type === "file") {
          // Get the file content
          const { data: fileContent } = await octokit.rest.repos.getContent({
            owner: "farcasterxyz",
            repo: "frames-v2-demo",
            path: item.path,
          });

          // Decode the base64 content
          const content = Buffer.from((fileContent as any).content, "base64").toString("utf-8");

          // Create the file in the new repository
          await octokit.rest.repos.createOrUpdateFileContents({
            owner: newRepoOwner,
            repo: newRepoName,
            path: item.path,
            message: `Initial commit: Copy ${item.path} from frames-v2-demo`,
            content: Buffer.from(content).toString("base64"), // Re-encode as base64
          });

          console.log(`Copied file: ${item.path}`);
        } else if (item.type === "dir") {
          // Recursively handle directories
          const { data: dirContents } = await octokit.rest.repos.getContent({
            owner: "farcasterxyz",
            repo: "frames-v2-demo",
            path: item.path,
          });

          if (Array.isArray(dirContents)) {
            for (const dirItem of dirContents) {
              if (dirItem.type === "file") {
                // Get the file content
                const { data: dirFileContent } = await octokit.rest.repos.getContent({
                  owner: "farcasterxyz",
                  repo: "frames-v2-demo",
                  path: dirItem.path,
                });

                // Decode the base64 content
                const dirContent = Buffer.from((dirFileContent as any).content, "base64").toString("utf-8");

                // Create the file in the new repository
                await octokit.rest.repos.createOrUpdateFileContents({
                  owner: newRepoOwner,
                  repo: newRepoName,
                  path: dirItem.path,
                  message: `Initial commit: Copy ${dirItem.path} from frames-v2-demo`,
                  content: Buffer.from(dirContent).toString("base64"), // Re-encode as base64
                });

                console.log(`Copied file: ${dirItem.path}`);
              }
            }
          }
        }
      }
    }

    console.log("Copied all contents to new repository");

    // Step 4: Create a Vercel project linked to the new repository
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
      }),
    });

    if (!vercelResponse.ok) {
      const vercelError = await vercelResponse.json();
      console.error("Vercel project creation failed:", vercelError);
      throw new Error("Failed to create Vercel project");
    }

    const vercelProject = await vercelResponse.json();
    console.log("Created Vercel project:", vercelProject);

    // Step 5: Trigger a deployment
    const deployment = await triggerVercelDeployment(
      sanitizedProjectName,
      vercelProject.link.repoId
    );
    console.log("Triggered Vercel deployment:", deployment);

    // Return the created project, repository URL, and Vercel deployment URL
    const newProject = {
      projectName,
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
