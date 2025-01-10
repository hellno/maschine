export interface TemplateCustomizationRequest {
  prompt: string
  userContext: Record<string, any>
}

export interface TemplateCustomizationResponse {
  success: boolean
  result?: string
  error?: string
}
