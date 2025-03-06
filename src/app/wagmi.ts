import { createConfig, http } from "wagmi";
import { base, optimism } from "wagmi/chains";
import { farcasterFrame } from "@farcaster/frame-wagmi-connector";
import { configureFabricSDK } from "@withfabric/protocol-sdks";

export const config = createConfig({
  chains: [base, optimism],
  transports: {
    [base.id]: http(),
    [optimism.id]: http(),
  },
  connectors: [farcasterFrame()],
});

configureFabricSDK({ wagmiConfig: config });
