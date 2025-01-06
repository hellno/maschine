import { NextResponse } from "next/server";
import { Octokit } from "octokit";

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

    // Return the created project and repository URL
    const newProject = {
      projectName,
      description,
      repoUrl: newRepoUrl,
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
