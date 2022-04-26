import { Directive, TemplateRef, ViewContainerRef } from '@angular/core';

@Directive({
  selector: '[gpfTableCellContent]'
})
export class GpfTableCellContentDirective {
  public constructor(
    public readonly templateRef: TemplateRef<any>,
    public readonly viewContainer: ViewContainerRef
  ) { }
}
