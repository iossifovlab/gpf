import { ContentChild, ViewChildren, ViewChild, HostListener, ChangeDetectorRef,
  Output, EventEmitter, Input, Directive, Component, OnInit, ContentChildren,
  QueryList, TemplateRef, ViewContainerRef, ComponentFactoryResolver,
  AfterViewInit, Query, ElementRef
} from '@angular/core';

import { GpfTableSubheaderComponent } from './subheader.component';
import { GpfTableContentHeaderComponent } from './header.component';
import { GpfTableCellContentDirective } from './content.directive';
import { GpfTableCellContentComponent } from './cell.component';
import { GpfTableLegendDirective } from './legend.directive';

@Component({
  selector: 'gpf-table-column',
  template: '',
})
export class GpfTableColumnComponent {
  @ContentChildren(GpfTableContentHeaderComponent) headerChildren: QueryList<GpfTableContentHeaderComponent>;
  @ContentChildren(GpfTableCellContentComponent) cellContentChildren: QueryList<GpfTableCellContentComponent>;
  public width = 0;

  constructor(viewContainer: ViewContainerRef) {
  }
}
