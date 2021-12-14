import { Pipe, PipeTransform } from '@angular/core';

@Pipe({name: 'split'})
export class SplitPipe implements PipeTransform {
  transform(text: string, separator: string): string[] {
    return text.split(separator);
  }
}
