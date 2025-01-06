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

    // Create a new GitHub repository
    const repoResponse = await octokit.rest.repos.createForAuthenticatedUser({
      name: projectName,
      description,
      private: false, // Set to true for private repositories
      auto_init: true, // Initialize the repository with a README
    });

    const repoUrl = repoResponse.data.html_url;

    // Return the created project and repository URL
    const newProject = {
      id: Math.random().toString(36).substring(7), // Generate a random ID
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
