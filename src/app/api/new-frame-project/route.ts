import { NextResponse } from "next/server";

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

    // Simulate creating a new frame project (replace with your actual logic)
    const newProject = {
      id: Math.random().toString(36).substring(7), // Generate a random ID
      projectName,
      description,
      createdAt: new Date().toISOString(),
    };

    // Return the created project
    return NextResponse.json(newProject, { status: 201 });
  } catch (error) {
    console.error("Error creating new frame project:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
