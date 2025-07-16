import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
    name: 'encodeUriComponent',
    standalone: false
})
export class EncodeUriComponentPipe implements PipeTransform {
  public transform(input: string): string {
    return encodeURIComponent(input);
  }
}
