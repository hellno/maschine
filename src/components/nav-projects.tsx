"use client";

import Link from "next/link";
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "~/components/ui/sidebar";
import { Project } from "~/lib/types";

export function NavProjects({
  projects,
  isLoading,
}: {
  projects: Project[];
  isLoading: boolean;
}) {
  const { isMobile, toggleSidebar } = useSidebar();

  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden">
      <SidebarGroupLabel>Projects</SidebarGroupLabel>
      <SidebarMenu className="gap-y-2">
        {isLoading ? (
          <SidebarMenuItem>
            <SidebarMenuButton asChild className="text-xl">
              <span>Loading...</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        ) : null}
        {projects.map((item) => (
          <SidebarMenuItem key={item.id}>
            <SidebarMenuButton asChild className="text-xl">
              <Link
                href={`/projects/${item.id}`}
                onClick={() => isMobile && toggleSidebar()}
              >
                <span>{item.name}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  );
}
