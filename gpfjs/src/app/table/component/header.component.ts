import { ContentChild, ViewChildren, ViewChild, HostListener, ChangeDetectorRef,
  Output, EventEmitter, Input, Directive, Component, OnInit, ContentChildren,
  QueryList, TemplateRef, ViewContainerRef, ComponentFactoryResolver,
  AfterViewInit, Query, ElementRef
} from '@angular/core';

import { GpfTableSubheaderComponent } from './subheader.component';

@Component({
  selector: 'gpf-table-content-header',
  template: '',
})
export class GpfTableContentHeaderComponent extends GpfTableSubheaderComponent {
  @ContentChildren(GpfTableSubheaderComponent) subcolumnsChildren: QueryList<GpfTableSubheaderComponent>;
}
