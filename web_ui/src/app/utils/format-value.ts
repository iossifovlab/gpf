/**
 * Formats one value with a printf-style format string.
 *
 * Replaces the sprintf.js library for the format strings that GPF configs use:
 * `%s`, `%d`, `%f` and `%.Nf`, plus `%%` for a literal percent sign.
 * The output matches sprintf.js 1.1.2 for these specifiers.
 * Text that is not one of these specifiers is kept as it is.
 *
 * A precision above 100 is clamped to 100, so a bad configuration can
 * not make `toFixed` throw a `RangeError`.
 */
const PLACEHOLDER = /%%|%(?:\.(\d+))?([sdf])/g;
// `Number.prototype.toFixed` throws a RangeError outside 0..100.
const MAX_PRECISION = 100;

function withSign(value: unknown, digits: string): string {
  // sprintf.js prints the sign from the comparison `value >= 0`, not from the digits.
  return (value as number) >= 0 ? digits : '-' + digits.replace(/^[+-]/, '');
}

function formatNumber(value: unknown, type: string, precision: string | undefined): string {
  if (typeof value !== 'number' && isNaN(value as number)) {
    throw new TypeError(`[formatValue] expecting number but found ${typeof value}`);
  }
  if (type === 'd') {
    return withSign(value, String(parseInt(value as string, 10)));
  }
  const number = parseFloat(value as string);
  if (precision === undefined) {
    return withSign(value, String(number));
  }
  return withSign(value, number.toFixed(Math.min(Number(precision), MAX_PRECISION)));
}

export function formatValue(format: string, value: unknown): string {
  return format.replace(PLACEHOLDER, (match: string, precision: string | undefined, type: string | undefined) => {
    if (match === '%%') {
      return '%';
    }
    if (type === 's') {
      // sprintf.js `%s` stringifies any value with `String`, objects too.
      // eslint-disable-next-line @typescript-eslint/no-base-to-string
      return String(value);
    }
    return formatNumber(value, type, precision);
  });
}
