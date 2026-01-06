import { describe, it, expect } from 'vitest'
import { snakeToCamel, camelToSnake, transformKeysToCamel } from './transformers'

describe('snakeToCamel', () => {
  it('converts simple snake_case to camelCase', () => {
    expect(snakeToCamel('user_name')).toBe('userName')
    expect(snakeToCamel('api_key_id')).toBe('apiKeyId')
  })

  it('handles strings with numbers after underscore', () => {
    expect(snakeToCamel('volume_24h')).toBe('volume24h')
    expect(snakeToCamel('price_1d')).toBe('price1d')
    expect(snakeToCamel('data_7d_ago')).toBe('data7dAgo')
  })

  it('handles strings without underscores', () => {
    expect(snakeToCamel('username')).toBe('username')
    expect(snakeToCamel('id')).toBe('id')
  })

  it('handles empty string', () => {
    expect(snakeToCamel('')).toBe('')
  })
})

describe('camelToSnake', () => {
  it('converts camelCase to snake_case', () => {
    expect(camelToSnake('userName')).toBe('user_name')
    expect(camelToSnake('apiKeyId')).toBe('api_key_id')
  })

  it('handles strings with numbers', () => {
    expect(camelToSnake('volume24h')).toBe('volume24h')
  })

  it('handles strings without uppercase', () => {
    expect(camelToSnake('username')).toBe('username')
  })
})

describe('transformKeysToCamel', () => {
  it('transforms object keys from snake_case to camelCase', () => {
    // Note: numeric strings are converted to numbers by transformKeysToCamel
    const input = { user_name: 'John', api_key: 'abc123' }
    const output = transformKeysToCamel(input)
    expect(output).toEqual({ userName: 'John', apiKey: 'abc123' })
  })

  it('handles keys with numbers after underscore', () => {
    const input = { volume_24h: 1000000, price_1h: 50000 }
    const output = transformKeysToCamel(input)
    expect(output).toEqual({ volume24h: 1000000, price1h: 50000 })
  })

  it('handles nested objects', () => {
    const input = { market_data: { volume_24h: 1000000, price_change_1d: 5.5 } }
    const output = transformKeysToCamel(input)
    expect(output).toEqual({ marketData: { volume24h: 1000000, priceChange1d: 5.5 } })
  })

  it('handles arrays', () => {
    const input = [{ user_name: 'John' }, { user_name: 'Jane' }]
    const output = transformKeysToCamel(input)
    expect(output).toEqual([{ userName: 'John' }, { userName: 'Jane' }])
  })

  it('handles null and undefined', () => {
    expect(transformKeysToCamel(null)).toBe(null)
    expect(transformKeysToCamel(undefined)).toBe(undefined)
  })
})
