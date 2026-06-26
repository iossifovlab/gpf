import { Directive, TemplateRef, ViewContainerRef, inject } from '@angular/core';

@Directive({
  selector: '[gpfTableLegend]',
  standalone: false
})
export class GpfTableLegendDirective {
  readonly templateRef = inject<TemplateRef<unknown>>(TemplateRef);
  readonly viewContainer = inject(ViewContainerRef);
}
