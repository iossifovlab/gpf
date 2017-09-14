import { ContentChild, ViewChildren, ViewChild, HostListener, ChangeDetectorRef,
  Output, EventEmitter, Input, Directive, Component, OnInit, ContentChildren,
  QueryList, TemplateRef, ViewContainerRef, ComponentFactoryResolver,
  AfterViewInit, Query, ElementRef
} from '@angular/core';

@Directive({
  selector: '[gpfTableCellContent]'
})
export class GpfTableCellContentDirective {
  constructor(
    readonly templateRef: TemplateRef<any>,
    readonly viewContainer: ViewContainerRef
  ) { }
}
