"use client";

import { AppSidebar } from "~/components/app-sidebar";
import { Button } from "~/components/ui/button";
import { Separator } from "~/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  useSidebar,
} from "~/components/ui/sidebar";
import { useFrameSDK } from "~/hooks/useFrameSDK";
import { useMobileTheme } from "~/hooks/useMobileTheme";
import { Avatar, AvatarFallback, AvatarImage } from "~/components/ui/avatar";

const CustomSidebarTrigger = () => {
  const { toggleSidebar } = useSidebar();
  return (
    <Button
      data-sidebar="trigger"
      variant="ghost"
      size="icon"
      className="px-2 -ml-1"
      onClick={() => toggleSidebar()}
    >
      <svg
        className="size-4 shrink-0"
        data-testid="geist-icon"
        height="16"
        strokeLinejoin="round"
        viewBox="0 0 16 16"
        width="16"
        style={{ color: "currentcolor" }}
      >
        <path
          fillRule="evenodd"
          clipRule="evenodd"
          d="M1.75 2H1V3.5H1.75H14.25H15V2H14.25H1.75ZM1 7H1.75H9.25H10V8.5H9.25H1.75H1V7ZM1 12H1.75H11.25H12V13.5H11.25H1.75H1V12Z"
          fill="currentColor"
        ></path>
      </svg>
      <span className="sr-only">Toggle Sidebar</span>
    </Button>
  );
};

const Layout = ({ children }: { children: React.ReactNode }) => {
  const { context } = useFrameSDK();
  useMobileTheme();

  return (
    <div
      style={{
        paddingTop: context?.client.safeAreaInsets?.top ?? 0,
        paddingBottom: context?.client.safeAreaInsets?.bottom ?? 0,
        paddingLeft: context?.client.safeAreaInsets?.left ?? 0,
        paddingRight: context?.client.safeAreaInsets?.right ?? 0,
      }}
    >
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12">
            <div className="flex items-center gap-2 px-4 w-[calc(100%-3rem)]">
              <CustomSidebarTrigger />
              <Separator orientation="vertical" className="mr-2 h-4" />
              <div className="flex justify-between items-center min-w-full">
                <span className="font-normal text-foreground">Maschine</span>
                <div className="flex items-center gap-2 max-w-[calc(40%)] mr-2">
                  <Avatar className="h-8 w-8 rounded-lg">
                    <AvatarImage
                      src={context?.user?.pfpUrl}
                      alt={context?.user?.username}
                    />
                    <AvatarFallback>
                      {context?.user?.username?.substring(0, 2) || "m"}
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-semibold">
                      {context?.user?.username}
                    </span>
                    <span className="truncate text-xs">
                      {context?.user?.displayName}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </header>
          <div className="flex flex-1 flex-col gap-4">{children}</div>
        </SidebarInset>
      </SidebarProvider>
    </div>
  );
};
export default Layout;
