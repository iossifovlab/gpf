import { ValidationArguments, ValidatorConstraint, ValidatorConstraintInterface } from 'class-validator';

@ValidatorConstraint({ name: 'customText', async: false })
export class RegionsFilterValidator implements ValidatorConstraintInterface {
  public validate(text: string, args: ValidationArguments): boolean {
    if (!text) {
      return null;
    }

    let valid = true;
    text = text.replace(/,(?![0-9]{3}\D{1})/g, '\n');
    const regions = text.split('\n')
      .map(t => t.trim())
      .filter(t => Boolean(t));

    if (regions.length === 0) {
      valid = false;
    }

    for (const region of regions) {
      valid = valid && this.isRegionValid(region, args.object['genome'] as string);
    }

    return valid;
  }

  private isRegionValid(region: string, genome: string): boolean {
    region = region.replaceAll(',', '');
    let chromRegex = '(2[0-2]|1[0-9]|[0-9]|X|Y)';
    if (genome === 'hg38') {
      chromRegex = 'chr' + chromRegex;
    }
    const lineRegex = `${chromRegex}:([0-9]+)(?:-([0-9]+))?|${chromRegex}`;

    const match = region.match(new RegExp(lineRegex, 'i'));
    if (match === null || match[0] !== region) {
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
