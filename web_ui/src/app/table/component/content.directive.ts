import { Directive, TemplateRef, ViewContainerRef, inject } from '@angular/core';

@Directive({
  selector: '[gpfTableCellContent]',
  standalone: false
})
export class GpfTableCellContentDirective {
  public readonly templateRef = inject<TemplateRef<unknown>>(TemplateRef);
  public readonly viewContainer = inject(ViewContainerRef);
}
