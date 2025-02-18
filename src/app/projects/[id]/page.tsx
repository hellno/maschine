import dynamic from "next/dynamic";

const ProjectDetailView = dynamic(
  () => import("~/components/ProjectDetailView")
);

export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const projectId = (await params).id;

  return <ProjectDetailView projectId={projectId} />;
}
