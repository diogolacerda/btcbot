/**
 * Bot Control Hook (FE-DASH-004)
 *
 * TanStack Query mutations for bot control actions with integrated
 * toast notifications and cache invalidation.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { dashboardKeys } from './useDashboardData'
import * as botControlService from '@/services/botControl'

export type BotAction = 'start' | 'stop' | 'pause' | 'resume'

interface UseBotControlOptions {
  /** Callback after any successful action */
  onSuccess?: (action: BotAction) => void
  /** Callback after any failed action */
  onError?: (action: BotAction, error: Error) => void
}

/**
 * Hook providing bot control mutations with automatic notifications.
 *
 * Features:
 * - Toast notifications for success/error states
 * - Automatic cache invalidation of bot status
 * - Loading states for all actions
 * - Combined isPending state for disabling controls
 */
export function useBotControl(options?: UseBotControlOptions) {
  const queryClient = useQueryClient()

  const invalidateBotStatus = () => {
    queryClient.invalidateQueries({ queryKey: dashboardKeys.botStatus() })
    queryClient.invalidateQueries({ queryKey: dashboardKeys.activity('today') })
  }

  const startBot = useMutation({
    mutationFn: botControlService.startBot,
    onSuccess: () => {
      toast.success('Bot Started', {
        description: 'Trading bot is now active and placing orders.',
      })
      invalidateBotStatus()
      options?.onSuccess?.('start')
    },
    onError: (error: Error) => {
      toast.error('Failed to Start Bot', {
        description: error.message || 'An unexpected error occurred.',
      })
      options?.onError?.('start', error)
    },
  })

  const stopBot = useMutation({
    mutationFn: botControlService.stopBot,
    onSuccess: () => {
      toast.success('Bot Stopped', {
        description: 'All pending orders cancelled. Open positions remain active.',
      })
      invalidateBotStatus()
      options?.onSuccess?.('stop')
    },
    onError: (error: Error) => {
      toast.error('Failed to Stop Bot', {
        description: error.message || 'An unexpected error occurred.',
      })
      options?.onError?.('stop', error)
    },
  })

  const pauseBot = useMutation({
    mutationFn: botControlService.pauseBot,
    onSuccess: () => {
      toast.success('Bot Paused', {
        description: 'No new orders will be placed. Existing positions preserved.',
      })
      invalidateBotStatus()
      options?.onSuccess?.('pause')
    },
    onError: (error: Error) => {
      toast.error('Failed to Pause Bot', {
        description: error.message || 'An unexpected error occurred.',
      })
      options?.onError?.('pause', error)
    },
  })

  const resumeBot = useMutation({
    mutationFn: botControlService.resumeBot,
    onSuccess: () => {
      toast.success('Bot Resumed', {
        description: 'Trading bot resumed normal operations.',
      })
      invalidateBotStatus()
      options?.onSuccess?.('resume')
    },
    onError: (error: Error) => {
      toast.error('Failed to Resume Bot', {
        description: error.message || 'An unexpected error occurred.',
      })
      options?.onError?.('resume', error)
    },
  })

  return {
    startBot,
    stopBot,
    pauseBot,
    resumeBot,
    /** True if any control action is in progress */
    isPending:
      startBot.isPending ||
      stopBot.isPending ||
      pauseBot.isPending ||
      resumeBot.isPending,
  }
}
