import { Directive, TemplateRef, ViewContainerRef, inject } from '@angular/core';

@Directive({
  selector: '[gpfTableCellContent]',
  standalone: false
})
export class GpfTableCellContentDirective {
  readonly templateRef = inject<TemplateRef<unknown>>(TemplateRef);
  readonly viewContainer = inject(ViewContainerRef);
}
