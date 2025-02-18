"use client";

import { ChevronRight, type LucideIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { render } from "react-dom";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "~/components/ui/collapsible";
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "~/components/ui/sidebar";

type NavItem = {
  title: string;
  url: string;
  icon?: LucideIcon;
  isActive?: boolean;
  items?: {
    title: string;
    url: string;
  }[];
};

export function NavMain({ items }: { items: NavItem[] }) {
  const router = useRouter();
  const renderMainItemButton = (item: NavItem) => (
    <SidebarMenuButton
      tooltip={item.title}
      onClick={item.url ? () => router.push(item.url) : undefined}
    >
      {item.icon && <item.icon />}
      <span>{item.title}</span>
      <ChevronRight className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
    </SidebarMenuButton>
  );

  return (
    <SidebarGroup>
      <SidebarGroupLabel>Maschine</SidebarGroupLabel>
      <SidebarMenu>
        {items.map((item) => (
          <Collapsible
            key={item.title}
            asChild
            defaultOpen={item.isActive}
            className="group/collapsible"
          >
            <SidebarMenuItem>
              {item?.items ? (
                <>
                  <CollapsibleTrigger asChild>
                    {renderMainItemButton(item)}
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <SidebarMenuSub>
                      {item.items?.map((subItem) => (
                        <SidebarMenuSubItem key={subItem.title}>
                          <SidebarMenuSubButton asChild>
                            <a href={subItem.url}>
                              <span>{subItem.title}</span>
                            </a>
                          </SidebarMenuSubButton>
                        </SidebarMenuSubItem>
                      ))}
                    </SidebarMenuSub>
                  </CollapsibleContent>
                </>
              ) : (
                renderMainItemButton(item)
              )}
            </SidebarMenuItem>
          </Collapsible>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  );
}
