import { Pipe, PipeTransform } from '@angular/core';

@Pipe({name: 'boldMatching'})
export class BoldMatchingPipe implements PipeTransform {
  transform(input: string, match: string): string {
    if (!match ||  match.length === 0) {
      return input;
    }

    let re = new RegExp('(' + match + ')', "ig");
    return input.replace(re, '<b>$1</b>');
  }
}
