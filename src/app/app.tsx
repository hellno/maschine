"use client";

import dynamic from "next/dynamic";

const Frameception = dynamic(() => import("~/components/Frameception"), {
  ssr: false,
});

export default function App() {
  return <Frameception />;
}
