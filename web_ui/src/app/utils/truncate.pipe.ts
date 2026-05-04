import { Pipe, PipeTransform } from '@angular/core';

/**
 * Truncate pipe with ellipsis
 */
@Pipe({
  name: 'truncate',
  standalone: false
})
export class TruncatePipe implements PipeTransform {
  public transform(value: string, limit: number, ellipsis = '...'): string {
    return value?.length > limit ? value.substring(0, limit) + ellipsis : value;
  }
}
