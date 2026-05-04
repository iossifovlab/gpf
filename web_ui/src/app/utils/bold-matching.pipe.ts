import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'boldMatching',
  standalone: false
})
export class BoldMatchingPipe implements PipeTransform {
  public transform(input: string, match: string): string {
    if (!match || match.length === 0) {
      return input;
    }

    const re = new RegExp('(' + this.escapeRegExp(match) + ')', 'ig');
    return input.replace(re, '<b>$1</b>');
  }

  public escapeRegExp(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
}
