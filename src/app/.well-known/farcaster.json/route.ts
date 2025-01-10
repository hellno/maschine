export async function GET() {
  const appUrl = process.env.NEXT_PUBLIC_URL;
  console.log('appUrl', appUrl);
  const config = {
    accountAssociation: {
      "header": "eyJmaWQiOjEzNTk2LCJ0eXBlIjoiY3VzdG9keSIsImtleSI6IjB4ODE3MzE4RDZmRkY2NkExOGQ4M0ExMzc2QTc2RjZlMzBCNDNjODg4OSJ9",
      "payload": "eyJkb21haW4iOiJpbW1lZGlhdGVseS10dnMtZXhpc3RpbmctaGltLnRyeWNsb3VkZmxhcmUuY29tIn0",
      "signature": "MHgyZTE2ODliZTE4MWIwZjE2ZWM4MGZjZDk5NjhmOWUwMjE0ODZhNThkOTAzODgzMGI3YmRlZmE1NmNlYjEyMzEwMzg0M2Q2MWU0MzU2YTRkY2Q4MDAwNTI5NjUxMTJjZWRkZWNmZWVlMDg3ZmJmNWY1NThiNDE5ODMyZmQ1NmM3YzFi"
    },
    frame: {
      version: "1",
      name: "Frameception",
      iconUrl: `${appUrl}/icon.png`,
      homeUrl: appUrl,
      imageUrl: `${appUrl}/frames/hello/opengraph-image`,
      buttonTitle: "Launch Frame",
      splashImageUrl: `${appUrl}/splash.png`,
      splashBackgroundColor: "#f7f7f7",
      webhookUrl: `${appUrl}/api/webhook`,
    },
  };
  console.log('config', config);
  return Response.json(config);
}