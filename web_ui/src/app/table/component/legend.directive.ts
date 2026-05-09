import { Directive, TemplateRef, ViewContainerRef } from '@angular/core';

@Directive({
  selector: '[gpfTableLegend]',
  standalone: false
})
export class GpfTableLegendDirective {
  public constructor(
    public readonly templateRef: TemplateRef<unknown>,
    public readonly viewContainer: ViewContainerRef
  ) { }
}
