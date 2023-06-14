import { ValidationArguments, ValidatorConstraint, ValidatorConstraintInterface } from 'class-validator';

@ValidatorConstraint({ name: 'customText', async: false })
export class RegionsFilterValidator implements ValidatorConstraintInterface {
  public validate(text: string, args: ValidationArguments): boolean {
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
      valid = valid && this.isValid(line, args.object['genome'] as string);
    }

    return valid;
  }

  private isValid(line: string, genome: string): boolean {
    let chromRegex = '(2[0-2]|1[0-9]|[0-9]|X|Y)';
    if (genome === 'hg38') {
      chromRegex = 'chr' + chromRegex;
    }
    const lineRegex = `${chromRegex}:([0-9]+)(?:-([0-9]+))?|${chromRegex}`;


    const match = line.match(new RegExp(lineRegex, 'i'));
    if (match === null || match[0] !== line) {
      return false;
    }

    if (
      match.length >= 3
      && match[2]
      && match[3]
      && Number(match[2].replace(',', '')) > Number(match[3].replace(',', ''))
    ) {
      return false;
    }

    return true;
  }

  public defaultMessage(): string {
    return 'Invalid region!';
  }
}
