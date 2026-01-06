// Transformers for converting between backend (snake_case) and frontend (camelCase)
// Also handles type conversions like Decimal -> number

/**
 * Convert snake_case string to camelCase
 * Examples:
 *   snake_to_camel('user_name') => 'userName'
 *   snake_to_camel('api_key_id') => 'apiKeyId'
 *   snake_to_camel('volume_24h') => 'volume24h'
 */
export function snakeToCamel(str: string): string {
  return str.replace(/_([a-z0-9])/g, (_, char) => char.toUpperCase())
}

/**
 * Convert camelCase string to snake_case
 * Examples:
 *   camel_to_snake('userName') => 'user_name'
 *   camel_to_snake('apiKeyId') => 'api_key_id'
 */
export function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`)
}

/**
 * Recursively transform object keys from snake_case to camelCase
 * Also converts string representations of Decimals to numbers
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function transformKeysToCamel<T = any>(obj: any): T {
  if (obj === null || obj === undefined) {
    return obj
  }

  if (Array.isArray(obj)) {
    return obj.map((item) => transformKeysToCamel(item)) as T
  }

  if (typeof obj === 'object' && obj.constructor === Object) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const result: Record<string, any> = {}

    for (const [key, value] of Object.entries(obj)) {
      const camelKey = snakeToCamel(key)
      result[camelKey] = transformKeysToCamel(value)
    }

    return result as T
  }

  // Convert string decimals to numbers if they look like numbers
  if (typeof obj === 'string' && /^-?\d+\.?\d*$/.test(obj)) {
    const num = Number(obj)
    if (!isNaN(num)) {
      return num as T
    }
  }

  return obj
}

/**
 * Recursively transform object keys from camelCase to snake_case
 * For sending data to the backend API
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function transformKeysToSnake<T = any>(obj: any): T {
  if (obj === null || obj === undefined) {
    return obj
  }

  if (Array.isArray(obj)) {
    return obj.map((item) => transformKeysToSnake(item)) as T
  }

  if (typeof obj === 'object' && obj.constructor === Object) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const result: Record<string, any> = {}

    for (const [key, value] of Object.entries(obj)) {
      const snakeKey = camelToSnake(key)
      result[snakeKey] = transformKeysToSnake(value)
    }

    return result as T
  }

  return obj
}

/**
 * Convert Decimal string or number to a JavaScript number
 * Handles both string representations and actual numbers
 */
export function decimalToNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined) {
    return null
  }

  if (typeof value === 'number') {
    return value
  }

  const num = Number(value)
  return isNaN(num) ? null : num
}

/**
 * Format number as Decimal string with fixed precision
 * Useful when sending data back to the backend that expects Decimal
 */
export function numberToDecimalString(value: number, precision: number = 2): string {
  return value.toFixed(precision)
}

/**
 * Safe parser for API responses that transforms keys and handles errors
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function parseApiResponse<T>(response: any): T {
  try {
    return transformKeysToCamel<T>(response)
  } catch (error) {
    console.error('Failed to parse API response:', error)
    throw new Error('Invalid API response format')
  }
}

/**
 * Safe serializer for API requests that transforms keys
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function serializeApiRequest<T>(data: any): T {
  try {
    return transformKeysToSnake<T>(data)
  } catch (error) {
    console.error('Failed to serialize API request:', error)
    throw new Error('Invalid request data format')
  }
}
