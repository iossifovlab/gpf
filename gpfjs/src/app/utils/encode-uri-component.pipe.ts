import { Pipe, PipeTransform } from '@angular/core';

@Pipe({name: 'encodeUriComponent'})
export class EncodeUriComponentPipe implements PipeTransform {
  transform(input: string): string {
    return encodeURIComponent(input);
  }
}
