import { ImageResponse } from "next/og";

export const alt = "Frameception";
export const size = {
  width: 600,
  height: 400,
};

export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div tw="h-full w-full flex flex-col justify-center items-center relative bg-white">
        <h1 tw="text-6xl">Frameception</h1>
        <h3 tw="text-2xl">Farcaster frame to build Farcaster frames</h3>
      </div>
    ),
    {
      ...size,
    }
  );
}
