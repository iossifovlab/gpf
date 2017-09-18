import { Directive, TemplateRef, ViewContainerRef } from '@angular/core';

@Directive({
  selector: '[gpfTableCellContent]'
})
export class GpfTableCellContentDirective {
  constructor(
    readonly templateRef: TemplateRef<any>,
    readonly viewContainer: ViewContainerRef
  ) { }
}
