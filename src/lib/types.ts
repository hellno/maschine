import { FrameContext } from "@farcaster/frame-sdk"

export interface TemplateCustomizationRequest {
  prompt: string
  userContext: FrameContext
}

export interface TemplateCustomizationResponse {
  success: boolean
  result?: string
  error?: string
}
