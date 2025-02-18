import { useFrameSDK } from "~/hooks/useFrameSDK";

import dynamic from "next/dynamic";
import WelcomeHero from "./WelcomeHero";

const DebugView = dynamic(() => import("~/components/DebugView"), {
  ssr: false,
});

export default function Frameception() {

  const renderDebugView = () => {
    if (process.env.NODE_ENV === "development") {
      return <DebugView />;
    }
    if (process.env.NEXT_PUBLIC_URL?.endsWith("cloudflare.com")) {
      return <DebugView />;
    }
  };
  return (

      <div className="mx-auto py-2 px-2 md:px-4 max-w-3xl text-center">
        <WelcomeHero />
        {renderDebugView()}
      </div>
        );
}
