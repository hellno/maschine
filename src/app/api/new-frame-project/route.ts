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

    console.log("Creating new fork with data", { projectName, description });

    // Fork the frames-v2-demo repository
    const forkResponse = await octokit.rest.repos.createFork({
      owner: "farcasterxyz",
      repo: "frames-v2-demo",
      name: projectName, // Use the project name as the new repository name
      description, // Set the repository description
    });

    console.log("Forked repository:", forkResponse.data);
    const repoUrl = forkResponse.data.html_url;

    // Return the created project and repository URL
    const newProject = {
      projectName,
      description,
      repoUrl,
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
