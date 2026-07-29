export interface MessageTask {
  id: string
  name: string
  message_type: number
  message_template: string
  web_hook_url: string
  mps_id: string
  status: number
  cron_exp?: string
  created_at: string
  updated_at: string
}

export interface MessageTaskCreate {
  name: string
  message_type: number
  message_template: string
  web_hook_url: string
  mps_id: string
  status?: number
  cron_exp?: string
}

export type MessageTaskUpdate = Partial<MessageTaskCreate>
