import { Directive, TemplateRef, ViewContainerRef, inject } from '@angular/core';

@Directive({
  selector: '[gpfTableLegend]',
  standalone: false
})
export class GpfTableLegendDirective {
  public readonly templateRef = inject<TemplateRef<unknown>>(TemplateRef);
  public readonly viewContainer = inject(ViewContainerRef);
}
