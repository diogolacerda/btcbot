/**
 * Zod Validation Schema for Strategy Form (FE-STRAT-002)
 *
 * Defines validation rules that match backend StrategyCreate/StrategyUpdate schemas.
 * Used with React Hook Form via @hookform/resolvers.
 */

import { z } from 'zod'
import type { MarginMode, SpacingType, AnchorMode } from '@/types/api'

// ============================================================================
// Constants - Match backend constraints
// ============================================================================

export const MARGIN_MODES: MarginMode[] = ['crossed', 'isolated']
export const SPACING_TYPES: SpacingType[] = ['fixed', 'percentage']
export const ANCHOR_MODES: AnchorMode[] = ['none', 'hundred', 'thousand']

export const LEVERAGE_MIN = 1
export const LEVERAGE_MAX = 125
export const ORDER_SIZE_MIN = 1
export const TP_PERCENT_MIN = 0.01
export const TP_PERCENT_MAX = 10

// ============================================================================
// Form Schema
// ============================================================================

export const strategyFormSchema = z
  .object({
    // Basic Info
    name: z
      .string()
      .min(1, 'Name is required')
      .max(100, 'Name must be 100 characters or less'),
    symbol: z.string().min(1, 'Symbol is required'),

    // Risk Parameters
    leverage: z
      .number()
      .min(LEVERAGE_MIN, `Leverage must be at least ${LEVERAGE_MIN}x`)
      .max(LEVERAGE_MAX, `Leverage must be at most ${LEVERAGE_MAX}x`),
    orderSizeUsdt: z
      .number()
      .min(ORDER_SIZE_MIN, `Order size must be at least $${ORDER_SIZE_MIN}`),
    marginMode: z.enum(['crossed', 'isolated']),

    // Take Profit
    takeProfitPercent: z
      .number()
      .min(TP_PERCENT_MIN, `TP must be at least ${TP_PERCENT_MIN}%`)
      .max(TP_PERCENT_MAX, `TP must be at most ${TP_PERCENT_MAX}%`),

    // Dynamic TP
    tpDynamicEnabled: z.boolean(),
    tpDynamicBase: z.number().min(0.01, 'Base TP must be positive'),
    tpDynamicMin: z.number().min(0.01, 'Min TP must be positive'),
    tpDynamicMax: z.number().min(0.01, 'Max TP must be positive'),
    tpDynamicSafetyMargin: z.number().min(0, 'Safety margin cannot be negative'),
    tpDynamicCheckInterval: z
      .number()
      .int('Check interval must be a whole number')
      .min(1, 'Check interval must be at least 1 minute'),

    // Grid Settings
    spacingType: z.enum(['fixed', 'percentage']),
    spacingValue: z.number().min(0.01, 'Spacing value must be positive'),
    rangePercent: z
      .number()
      .min(0.1, 'Range must be at least 0.1%')
      .max(50, 'Range must be at most 50%'),
    maxTotalOrders: z
      .number()
      .int('Max orders must be a whole number')
      .min(1, 'At least 1 order required')
      .max(50, 'Maximum 50 orders allowed'),
    anchorMode: z.enum(['none', 'hundred', 'thousand']),
    anchorThreshold: z.number().min(1, 'Threshold must be at least 1'),
  })
  .refine(
    (data) => {
      // Dynamic TP validation: min <= base <= max
      if (data.tpDynamicEnabled) {
        return data.tpDynamicMin <= data.tpDynamicBase && data.tpDynamicBase <= data.tpDynamicMax
      }
      return true
    },
    {
      message: 'Dynamic TP values must be: min <= base <= max',
      path: ['tpDynamicBase'],
    }
  )

// ============================================================================
// Types
// ============================================================================

export type StrategyFormValues = z.infer<typeof strategyFormSchema>

// Default values for creating a new strategy
export const defaultStrategyValues: StrategyFormValues = {
  // Basic Info
  name: '',
  symbol: 'BTC-USDT',

  // Risk Parameters
  leverage: 10,
  orderSizeUsdt: 100,
  marginMode: 'crossed',

  // Take Profit
  takeProfitPercent: 0.5,

  // Dynamic TP
  tpDynamicEnabled: false,
  tpDynamicBase: 0.3,
  tpDynamicMin: 0.3,
  tpDynamicMax: 1.0,
  tpDynamicSafetyMargin: 0.05,
  tpDynamicCheckInterval: 60,

  // Grid Settings
  spacingType: 'fixed',
  spacingValue: 100,
  rangePercent: 5.0,
  maxTotalOrders: 10,
  anchorMode: 'none',
  anchorThreshold: 100,
}
