import { useQuery } from "@tanstack/react-query";

type Requirement = {
  idx: number;
  isValid: boolean;
  name: string;
  message?: string;
};

type AccessCheckResponse = {
  requirements: Requirement[];
  hasAccess: boolean;
  actionMessage?: string;
};

export function useAccessCheck(fid?: number, address?: string) {
  return useQuery<AccessCheckResponse>({
    queryKey: ["access", fid, address],
    queryFn: async () => {
      const response = await fetch("/api/check-access", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ fids: [fid], address }),
      });

      if (!response.ok) {
        throw new Error("Access check failed");
      }

      return response.json();
    },
    enabled: !!fid && !!address,
  });
}
