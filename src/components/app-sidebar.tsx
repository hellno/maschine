"use client";

import * as React from "react";
import { HelpCircle, Home, Sparkles } from "lucide-react";

import { NavMain } from "~/components/nav-main";
import { NavProjects } from "~/components/nav-projects";
import { NavUser } from "~/components/nav-user";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "~/components/ui/sidebar";
import { useFrameSDK } from "~/hooks/useFrameSDK";
import { useProjects } from "~/hooks/useProjects";

const data = {
  navMain: [
    {
      title: "Home",
      url: "/",
      icon: Home,
    },
    {
      title: "Frames",
      url: "",
      icon: Sparkles,
      isActive: true,
      items: [
        {
          title: "New",
          url: "/projects/new",
        },
        {
          title: "All",
          url: "/projects/all",
        },
      ],
    },
    {
      title: "Support",
      url: "https://warpcast.com/hellno.eth",
      icon: HelpCircle,
    },
    // {
    //   title: "Settings",
    //   url: "#",
    //   icon: Settings2,
    //   items: [
    //     {
    //       title: "General",
    //       url: "#",
    //     },
    //     {
    //       title: "Team",
    //       url: "#",
    //     },
    //     {
    //       title: "Billing",
    //       url: "#",
    //     },
    //     {
    //       title: "Limits",
    //       url: "#",
    //     },
    //   ],
    // },
  ],
  // projects: [
  //   {
  //     name: "Design Engineering",
  //     url: "#",
  //     icon: Frame,
  //   },
  //   {
  //     name: "Sales & Marketing",
  //     url: "#",
  //     icon: PieChart,
  //   },
  //   {
  //     name: "Travel",
  //     url: "#",
  //     icon: Map,
  //   },
  // ],
};

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { context } = useFrameSDK();
  const { isLoading: isLoadingProjects, projects } = useProjects(
    context?.user.fid,
  );

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        {context?.user && (
          <p className="text-sm font-semibold text-sidebar-accent-foreground">
            Hey {context.user.displayName}
          </p>
        )}
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        <NavProjects projects={projects} isLoading={isLoadingProjects} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={context?.user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
