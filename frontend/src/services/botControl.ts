/**
 * Bot Control Service (FE-DASH-004)
 *
 * API methods for controlling the trading bot:
 * - start: Begin trading operations
 * - stop: Halt all trading, cancel pending orders
 * - pause: Stop new orders, keep existing positions
 * - resume: Resume from paused state
 */

import { axiosInstance } from '@/lib/axios'
import { parseApiResponse } from '@/lib/transformers'
import type { BotStatusResponse } from '@/types/api'

export interface BotControlResponse {
  success: boolean
  message: string
  status: BotStatusResponse
}

/**
 * Start the trading bot.
 * Bot will begin executing the grid strategy.
 */
export async function startBot(): Promise<BotControlResponse> {
  const response = await axiosInstance.post('/bot/start')
  return parseApiResponse<BotControlResponse>(response.data)
}

/**
 * Stop the trading bot.
 * Cancels all pending orders but keeps open positions until TP is hit.
 */
export async function stopBot(): Promise<BotControlResponse> {
  const response = await axiosInstance.post('/bot/stop')
  return parseApiResponse<BotControlResponse>(response.data)
}

/**
 * Pause the trading bot.
 * Stops placing new orders but keeps existing positions and TP orders active.
 */
export async function pauseBot(): Promise<BotControlResponse> {
  const response = await axiosInstance.post('/bot/pause')
  return parseApiResponse<BotControlResponse>(response.data)
}

/**
 * Resume the trading bot from paused state.
 * Bot will continue placing orders according to strategy.
 */
export async function resumeBot(): Promise<BotControlResponse> {
  const response = await axiosInstance.post('/bot/resume')
  return parseApiResponse<BotControlResponse>(response.data)
}
