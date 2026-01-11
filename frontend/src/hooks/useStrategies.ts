/**
 * Strategy Data Fetching Hooks (FE-STRAT-001)
 *
 * TanStack Query hooks for fetching and managing strategies.
 * Includes hooks for CRUD operations and activation.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { axiosInstance } from '../lib/axios'
import { parseApiResponse, serializeApiRequest } from '../lib/transformers'
import type {
  StrategyResponse,
  StrategyCreateRequest,
  StrategyUpdateRequest,
  StrategyActivateResponse,
  MACDFilterConfigResponse,
  MACDFilterConfigUpdateRequest,
  EMAFilterConfigResponse,
  EMAFilterConfigUpdateRequest,
} from '../types/api'

// ============================================================================
// Query Keys - Centralized for cache invalidation
// ============================================================================

export const strategyKeys = {
  all: ['strategies'] as const,
  list: () => [...strategyKeys.all, 'list'] as const,
  detail: (id: string) => [...strategyKeys.all, 'detail', id] as const,
  macdFilter: (strategyId: string) =>
    [...strategyKeys.all, 'macd-filter', strategyId] as const,
  emaFilter: (strategyId: string) =>
    [...strategyKeys.all, 'ema-filter', strategyId] as const,
}

// ============================================================================
// Fetch Functions
// ============================================================================

async function fetchStrategies(): Promise<StrategyResponse[]> {
  const response = await axiosInstance.get('/strategies')
  const parsed = parseApiResponse<StrategyResponse[]>(response.data)
  return parsed
}

async function fetchStrategy(id: string): Promise<StrategyResponse> {
  const response = await axiosInstance.get(`/strategies/${id}`)
  return parseApiResponse<StrategyResponse>(response.data)
}

async function createStrategy(
  data: StrategyCreateRequest
): Promise<StrategyResponse> {
  const response = await axiosInstance.post(
    '/strategies',
    serializeApiRequest(data)
  )
  return parseApiResponse<StrategyResponse>(response.data)
}

async function updateStrategy(
  id: string,
  data: StrategyUpdateRequest
): Promise<StrategyResponse> {
  const response = await axiosInstance.patch(
    `/strategies/${id}`,
    serializeApiRequest(data)
  )
  return parseApiResponse<StrategyResponse>(response.data)
}

async function deleteStrategy(id: string): Promise<void> {
  await axiosInstance.delete(`/strategies/${id}`)
}

async function activateStrategy(id: string): Promise<StrategyActivateResponse> {
  const response = await axiosInstance.post(`/strategies/${id}/activate`)
  return parseApiResponse<StrategyActivateResponse>(response.data)
}

// ============================================================================
// useStrategies Hook - List all strategies
// ============================================================================

export interface UseStrategiesOptions {
  enabled?: boolean
}

/**
 * Fetch all strategies for the authenticated account.
 *
 * @example
 * const { data: strategies, isLoading, error } = useStrategies()
 */
export function useStrategies(options: UseStrategiesOptions = {}) {
  const { enabled = true } = options

  return useQuery({
    queryKey: strategyKeys.list(),
    queryFn: fetchStrategies,
    enabled,
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
  })
}

// ============================================================================
// useStrategy Hook - Get single strategy
// ============================================================================

export interface UseStrategyOptions {
  enabled?: boolean
}

/**
 * Fetch a single strategy by ID.
 *
 * @example
 * const { data: strategy, isLoading } = useStrategy(strategyId)
 */
export function useStrategy(id: string, options: UseStrategyOptions = {}) {
  const { enabled = true } = options

  return useQuery({
    queryKey: strategyKeys.detail(id),
    queryFn: () => fetchStrategy(id),
    enabled: enabled && !!id,
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
  })
}

// ============================================================================
// useCreateStrategy Mutation
// ============================================================================

/**
 * Create a new strategy.
 *
 * @example
 * const mutation = useCreateStrategy()
 * mutation.mutate({ name: 'My Strategy', leverage: 10 })
 */
export function useCreateStrategy() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createStrategy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: strategyKeys.all })
    },
  })
}

// ============================================================================
// useUpdateStrategy Mutation
// ============================================================================

/**
 * Update an existing strategy.
 *
 * @example
 * const mutation = useUpdateStrategy()
 * mutation.mutate({ id: 'strategy-id', data: { name: 'Updated Name' } })
 */
export function useUpdateStrategy() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: StrategyUpdateRequest }) =>
      updateStrategy(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: strategyKeys.all })
      queryClient.invalidateQueries({
        queryKey: strategyKeys.detail(variables.id),
      })
    },
  })
}

// ============================================================================
// useDeleteStrategy Mutation
// ============================================================================

/**
 * Delete a strategy.
 *
 * @example
 * const mutation = useDeleteStrategy()
 * mutation.mutate('strategy-id')
 */
export function useDeleteStrategy() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteStrategy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: strategyKeys.all })
    },
  })
}

// ============================================================================
// useActivateStrategy Mutation
// ============================================================================

/**
 * Activate a strategy (deactivates all others).
 *
 * @example
 * const mutation = useActivateStrategy()
 * mutation.mutate('strategy-id')
 */
export function useActivateStrategy() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: activateStrategy,
    onSuccess: () => {
      // Invalidate all strategies since activation changes multiple items
      queryClient.invalidateQueries({ queryKey: strategyKeys.all })
    },
  })
}

// ============================================================================
// MACD Filter Config Hooks (FE-STRAT-003)
// ============================================================================

async function fetchMACDFilterConfig(
  strategyId: string
): Promise<MACDFilterConfigResponse> {
  const response = await axiosInstance.get(
    `/strategies/${strategyId}/macd-filter`
  )
  return parseApiResponse<MACDFilterConfigResponse>(response.data)
}

async function updateMACDFilterConfig(
  strategyId: string,
  data: MACDFilterConfigUpdateRequest
): Promise<MACDFilterConfigResponse> {
  const response = await axiosInstance.patch(
    `/strategies/${strategyId}/macd-filter`,
    serializeApiRequest(data)
  )
  return parseApiResponse<MACDFilterConfigResponse>(response.data)
}

export interface UseMACDFilterConfigOptions {
  enabled?: boolean
}

/**
 * Fetch MACD filter configuration for a strategy.
 *
 * @example
 * const { data: macdConfig, isLoading } = useMACDFilterConfig(strategyId)
 */
export function useMACDFilterConfig(
  strategyId: string,
  options: UseMACDFilterConfigOptions = {}
) {
  const { enabled = true } = options

  return useQuery({
    queryKey: strategyKeys.macdFilter(strategyId),
    queryFn: () => fetchMACDFilterConfig(strategyId),
    enabled: enabled && !!strategyId,
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
  })
}

/**
 * Update MACD filter configuration for a strategy.
 *
 * @example
 * const mutation = useUpdateMACDFilterConfig()
 * mutation.mutate({
 *   strategyId: 'strategy-id',
 *   data: { enabled: true, fastPeriod: 12 }
 * })
 */
export function useUpdateMACDFilterConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      strategyId,
      data,
    }: {
      strategyId: string
      data: MACDFilterConfigUpdateRequest
    }) => updateMACDFilterConfig(strategyId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: strategyKeys.macdFilter(variables.strategyId),
      })
    },
  })
}

// ============================================================================
// EMA Filter Config Hooks
// ============================================================================

async function fetchEMAFilterConfig(
  strategyId: string
): Promise<EMAFilterConfigResponse> {
  const response = await axiosInstance.get(
    `/strategies/${strategyId}/ema-filter`
  )
  return parseApiResponse<EMAFilterConfigResponse>(response.data)
}

async function updateEMAFilterConfig(
  strategyId: string,
  data: EMAFilterConfigUpdateRequest
): Promise<EMAFilterConfigResponse> {
  const response = await axiosInstance.patch(
    `/strategies/${strategyId}/ema-filter`,
    serializeApiRequest(data)
  )
  return parseApiResponse<EMAFilterConfigResponse>(response.data)
}

export interface UseEMAFilterConfigOptions {
  enabled?: boolean
}

/**
 * Fetch EMA filter configuration for a strategy.
 *
 * @example
 * const { data: emaConfig, isLoading } = useEMAFilterConfig(strategyId)
 */
export function useEMAFilterConfig(
  strategyId: string,
  options: UseEMAFilterConfigOptions = {}
) {
  const { enabled = true } = options

  return useQuery({
    queryKey: strategyKeys.emaFilter(strategyId),
    queryFn: () => fetchEMAFilterConfig(strategyId),
    enabled: enabled && !!strategyId,
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
  })
}

/**
 * Update EMA filter configuration for a strategy.
 *
 * @example
 * const mutation = useUpdateEMAFilterConfig()
 * mutation.mutate({
 *   strategyId: 'strategy-id',
 *   data: { enabled: true, period: 13 }
 * })
 */
export function useUpdateEMAFilterConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      strategyId,
      data,
    }: {
      strategyId: string
      data: EMAFilterConfigUpdateRequest
    }) => updateEMAFilterConfig(strategyId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: strategyKeys.emaFilter(variables.strategyId),
      })
    },
  })
}
