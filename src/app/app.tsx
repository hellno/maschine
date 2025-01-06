"use client";

import dynamic from "next/dynamic";

const Demo = dynamic(() => import("~/components/Frameception"), {
  ssr: false,
});

export default function App(
  { title }: { title?: string } = { title: "Frameception" }
) {
  return <Demo title={title} />;
}
