import { Pipe, PipeTransform } from '@angular/core';

@Pipe({name: 'encodeUri'})
export class EncodeUriPipe implements PipeTransform {
  transform(input: string): string {
    return encodeURI(input);
  }
}
