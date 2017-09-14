import { ContentChild, ViewChildren, ViewChild, HostListener, ChangeDetectorRef,
  Output, EventEmitter, Input, Directive, Component, OnInit, ContentChildren,
  QueryList, TemplateRef, ViewContainerRef, ComponentFactoryResolver,
  AfterViewInit, Query, ElementRef
} from '@angular/core';

import { GpfTableColumnComponent } from './column.component';
import { GpfTableSubheaderComponent } from './subheader.component';
import { GpfTableContentHeaderComponent } from './header.component';
import { GpfTableCellContentDirective } from './content.directive';
import { GpfTableCellContentComponent } from './cell.component';
import { GpfTableLegendDirective } from './legend.directive';

class DefaultComparator {
  constructor(private subcolumn: GpfTableSubheaderComponent) {
  }

  compare(a: any, b: any): Number {
    let leftVal = a[this.subcolumn.field];
    let rightVal = b[this.subcolumn.field];

    if (leftVal == null && rightVal == null) { return 0; }
    if (leftVal == null) { return -1; }
    if (rightVal == null) { return 1; }

    if (!isNaN(leftVal) && !isNaN(rightVal)) {
      return +leftVal - +rightVal;
    }

    return leftVal.localeCompare(rightVal);
  }
}
