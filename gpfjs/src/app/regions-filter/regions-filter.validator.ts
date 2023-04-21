import { DatasetsService } from 'app/datasets/datasets.service';
import { ValidatorConstraint, ValidatorConstraintInterface } from 'class-validator';

@ValidatorConstraint({ name: 'customText', async: false })
export class RegionsFilterValidator implements ValidatorConstraintInterface {
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
    let lineRegex = '([0-9]+):([0-9]+)(?:-([0-9]+))?';
    if (DatasetsService.currentGenome === 'hg38') {
      lineRegex = 'chr([0-9]+):([0-9]+)(?:-([0-9]+))?';
    }

    const match = line.match(new RegExp(lineRegex, 'i'));
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
