import { Directive, TemplateRef, ViewContainerRef } from '@angular/core';

@Directive({
  selector: '[gpfTableLegend]',
  standalone: false
})
export class GpfTableLegendDirective {
  public constructor(
    public readonly templateRef: TemplateRef<any>,
    public readonly viewContainer: ViewContainerRef
  ) { }
}
