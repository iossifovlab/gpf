import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
    name: 'join',
    standalone: false
})
export class JoinPipe implements PipeTransform {
  public transform(input: string[], sep = ','): string {
    return input.join(sep);
  }
}
