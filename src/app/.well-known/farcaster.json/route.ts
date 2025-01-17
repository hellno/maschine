export async function GET() {
  const appUrl = process.env.NEXT_PUBLIC_URL;
  console.log('appUrl', appUrl);
  const config = {
    accountAssociation: {
      "header": "eyJmaWQiOjEzNTk2LCJ0eXBlIjoiY3VzdG9keSIsImtleSI6IjB4ODE3MzE4RDZmRkY2NkExOGQ4M0ExMzc2QTc2RjZlMzBCNDNjODg4OSJ9",
      "payload": "eyJkb21haW4iOiJmYXJjYXN0ZXJmcmFtZWNlcHRpb24udmVyY2VsLmFwcCJ9",
      "signature": "MHhmN2JjMDgwMzhlYTU2ZDY4Njg3ODg3YjM4MTZlNDQ4NDc5YzUyODU1NjU5NTljZTE5MjQ4ZTExMDcwNjJhZTkwM2ExNTMyNGMzNmYyNjZkOGY2YjU3Yzc1ZTAzOWZkYTA5YmMzODZkNWM3NTYyZWYxMjZmNWY3MDEwNGMwMmFjMDFi"
    },
    frame: {
      version: "1",
      name: "Frameception",
      iconUrl: `${appUrl}/icon.png`,
      homeUrl: appUrl,
      imageUrl: `${appUrl}/og.png`,
      buttonTitle: "Launch Frame",
      splashImageUrl: `${appUrl}/splash.png`,
      splashBackgroundColor: "#555555",
      webhookUrl: `${appUrl}/api/webhook`,
    },
  };
  console.log('config', config);
  return Response.json(config);
}