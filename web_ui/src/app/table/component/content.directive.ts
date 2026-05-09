import { Directive, TemplateRef, ViewContainerRef } from '@angular/core';

@Directive({
  selector: '[gpfTableCellContent]',
  standalone: false
})
export class GpfTableCellContentDirective {
  public constructor(
    public readonly templateRef: TemplateRef<unknown>,
    public readonly viewContainer: ViewContainerRef
  ) { }
}
