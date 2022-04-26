import { Directive, TemplateRef } from '@angular/core';

@Directive({
  selector: '[gpf-searchable-select-template]',
})
export class SearchableSelectTemplateDirective {
  public constructor(public readonly templateRef: TemplateRef<any>) {}
}
