import { ContentChild, ViewChildren, ViewChild, HostListener, ChangeDetectorRef,
  Output, EventEmitter, Input, Directive, Component, OnInit, ContentChildren,
  QueryList, TemplateRef, ViewContainerRef, ComponentFactoryResolver,
  AfterViewInit, Query, ElementRef
} from '@angular/core';

import { GpfTableColumnComponent } from './column.component';
import { GpfTableContentHeaderComponent } from './header.component';
import { GpfTableCellContentDirective } from './content.directive';
import { GpfTableCellContentComponent } from './cell.component';
import { GpfTableLegendDirective } from './legend.directive';

@Component({
  selector: 'gpf-table-subheader',
  template: '',
})
export class GpfTableSubheaderComponent {
  @ContentChildren(GpfTableCellContentDirective) contentChildren: QueryList<GpfTableCellContentDirective>;
  @Input() field: string;
  @Input() caption: string;
  @Input() comparator: (leftVal: any, rightVal: any) => number = this.defaultComparator;
  @Input() sortable = true;

  contentTemplateRef: TemplateRef<any>;

  ngAfterContentInit() {
    if (this.contentChildren.first) {
      this.contentTemplateRef = this.contentChildren.first.templateRef;
    }
  }

  defaultComparator(a: any, b: any): number {
    let leftVal = a[this.field];
    let rightVal = b[this.field];

    if (leftVal == null && rightVal == null) { return 0; }
    if (leftVal == null) { return -1; }
    if (rightVal == null) { return 1; }

    if (!isNaN(leftVal) && !isNaN(rightVal)) {
      return +leftVal - +rightVal;
    }

    return leftVal.localeCompare(rightVal);
  }

  sort(data: any, ascending: boolean) {
    data.sort((a, b) => {
      if (ascending) {
        return this.comparator(a, b);
      } else {
        return this.comparator(b, a);
      }
    });
  }
}
