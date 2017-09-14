import { ContentChild, ViewChildren, ViewChild, HostListener, ChangeDetectorRef,
  Output, EventEmitter, Input, Directive, Component, OnInit, ContentChildren,
  QueryList, TemplateRef, ViewContainerRef, ComponentFactoryResolver,
  AfterViewInit, Query, ElementRef
} from '@angular/core';

import { GpfTableColumnComponent } from './column.component';
import { GpfTableSubheaderComponent } from './subheader.component';
import { GpfTableContentHeaderComponent } from './header.component';
import { GpfTableCellContentDirective } from './content.directive';
import { GpfTableLegendDirective } from './legend.directive';

@Component({
  selector: 'gpf-table-cell-content',
  template: '',
})
export class GpfTableCellContentComponent {
  @ContentChildren(GpfTableCellContentDirective) contentChildren: QueryList<GpfTableCellContentDirective>;
  @Input() field: string;
  contentTemplateRef: TemplateRef<any>;

  ngAfterContentInit() {
    if (this.contentChildren.first) {
      this.contentTemplateRef = this.contentChildren.first.templateRef;
    }
  }
}
