import { NextResponse } from "next/server";
import { Octokit } from "octokit";

interface VercelProject {
  id: string;
  name: string;
  url: string;
}

interface VercelDeployment {
  id: string;
  url: string;
  readyState: string;
}

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
        name: projectName,
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

    const vercelProject: VercelProject = await vercelResponse.json();
    console.log("Created Vercel project:", vercelProject);

    // Step 5: Trigger an initial deployment
    const deploymentResponse = await fetch(
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
            repo: `${newRepoOwner}/${newRepoName}`,
            ref: "main",
          },
        }),
      }
    );

    if (!deploymentResponse.ok) {
      const deploymentError = await deploymentResponse.json();
      console.error("Vercel deployment failed:", deploymentError);
      throw new Error("Failed to trigger Vercel deployment");
    }

    const deployment: VercelDeployment = await deploymentResponse.json();
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
