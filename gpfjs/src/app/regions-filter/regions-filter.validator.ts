import { ValidatorConstraint, ValidatorConstraintInterface } from 'class-validator';

@ValidatorConstraint({ name: 'customText', async: false })
export class RegionsFilterValidator implements ValidatorConstraintInterface {
  private static lineRegex = new RegExp('chr([0-9]+):([0-9]+)(?:-([0-9]+))?', 'i');

  public validate(text: string): boolean {
    if (!text) {
      return null;
    }

    let valid = true;
    const lines = text.split(/[\n,]/)
      .map(t => t.trim())
      .filter(t => Boolean(t));

    if (lines.length === 0) {
      valid = false;
    }

    for (const line of lines) {
      valid = valid && this.isValid(line);
    }

    return valid;
  }

  private isValid(line: string): boolean {
    const match = line.match(RegionsFilterValidator.lineRegex);
    if (match === null) {
      return false;
    }

    if (match[0] !== line) {
      return false;
    }

    if (
      match.length >= 3
      && match[1]
      && match[2]
      && Number(match[1].replace(',', '')) > Number(match[2].replace(',', ''))
    ) {
      return false;
    }

    return true;
  }

  public defaultMessage(): string {
    return 'Invalid region!';
  }
}
