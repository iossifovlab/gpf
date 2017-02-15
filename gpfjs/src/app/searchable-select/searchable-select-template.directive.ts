import { Directive, Component, Input, Output, EventEmitter, TemplateRef, ContentChild } from '@angular/core';

@Directive({
  selector: '[gpf-searchable-select-template]',
})
export class SearchableSelectTemplateDirective {
  constructor(
   readonly templateRef: TemplateRef<any>) {}
}
