import { formatValue } from './format-value';

describe('formatValue', () => {
  it('formats %s as the string form of the value', () => {
    expect(formatValue('%s', 'abc')).toBe('abc');
    expect(formatValue('%s', 1.5)).toBe('1.5');
    expect(formatValue('%s', null)).toBe('null');
  });

  it('formats %s of an object with String, like sprintf.js', () => {
    expect(formatValue('%s', [1, 2])).toBe('1,2');
    expect(formatValue('%s', { a: 1 })).toBe('[object Object]');
  });

  it('formats %d as the integer part of the value, like sprintf.js', () => {
    expect(formatValue('%d', 42)).toBe('42');
    expect(formatValue('%d', 3.9)).toBe('3');
    expect(formatValue('%d', '17')).toBe('17');
    expect(formatValue('%d', -3.9)).toBe('-3');
    expect(formatValue('%d', -0.5)).toBe('-0');
    expect(formatValue('%d', null)).toBe('NaN');
  });

  it('formats %f without a precision as the shortest number form, like sprintf.js', () => {
    expect(formatValue('%f', 0.1)).toBe('0.1');
    expect(formatValue('%f', 2)).toBe('2');
    expect(formatValue('%f', '1.250')).toBe('1.25');
    expect(formatValue('%f', -1.5)).toBe('-1.5');
  });

  it('formats %.2f with two decimals, like sprintf.js', () => {
    expect(formatValue('%.2f', 3.14159)).toBe('3.14');
    expect(formatValue('%.2f', '2.005')).toBe('2.00');
    expect(formatValue('%.2f', -0.001)).toBe('-0.00');
    expect(formatValue('%.2f', 1e21)).toBe('1e+21');
    expect(formatValue('%.2f', NaN)).toBe('-NaN');
    expect(formatValue('%.2f', null)).toBe('NaN');
  });

  it('formats %.3f with three decimals', () => {
    expect(formatValue('%.3f', 1e-7)).toBe('0.000');
    expect(formatValue('%.3f', 0.1235)).toBe('0.123');
  });

  it('formats %.5f with five decimals', () => {
    expect(formatValue('%.5f', 123.456789)).toBe('123.45679');
  });

  it('clamps a precision above 100 to 100 instead of throwing', () => {
    expect(formatValue('%.500f', 1)).toBe(formatValue('%.100f', 1));
    expect(formatValue('%.500f', 1)).toBe('1.' + '0'.repeat(100));
  });

  it('keeps the literal text around the specifier and prints %% as %', () => {
    expect(formatValue('value: %.2f%%', 0.5)).toBe('value: 0.50%');
  });

  it('throws a TypeError for a non-numeric value under %d or %f, like sprintf.js', () => {
    expect(() => formatValue('%d', 'abc')).toThrow(TypeError);
    expect(() => formatValue('%.2f', 'abc')).toThrow(TypeError);
  });
});
