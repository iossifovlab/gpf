import { ViewChild, HostListener, ChangeDetectorRef, Output, EventEmitter, Input, Directive, Component, OnInit, ContentChildren, QueryList, TemplateRef, ViewContainerRef, ComponentFactoryResolver } from '@angular/core';

// One bright day we should replace this with NgTemplateOutlet
@Component({
  selector: 'gpf-custom-template',
  template: ''
})
export class GpfCustomTemplateComponent {
  @Input() data: any;
  @Input() templateRef: TemplateRef<any>;

  constructor(private viewContainer: ViewContainerRef) { 
  }
  
  ngAfterContentInit() {
    let childView = this.viewContainer.createEmbeddedView(this.templateRef, {$implicit: this.data});
    childView.detectChanges();
  }
}

@Component({
  selector: 'gpf-table-cell',
  templateUrl: './table-cell.component.html'
})
export class GpfTableCell {
  @Input() columnInfo: GpfTableColumnComponent;
  @Input() data: any;

  constructor(private viewContainer: ViewContainerRef) { 
  }
}



@Component({
  selector: 'gpf-table-header',
  templateUrl: './table-header.component.html'
})
export class GpfTableHeader {
  @Input() columnInfo: GpfTableColumnComponent;
  @Output() sortingInfoChange = new EventEmitter();
  @Input() sortingInfo: SortInfo;

  constructor(private viewContainer: ViewContainerRef) { 
  }
  
  onSortClick(sortBySubcolumn: GpfTableSubcolumnComponent) {
    let sortInfo: SortInfo;
    if (this.sortingInfo && this.sortingInfo.sortBySubcolumn == sortBySubcolumn) {
      sortInfo = new SortInfo(sortBySubcolumn, !this.sortingInfo.sortOrderAsc);
    }
    else {
      sortInfo = new SortInfo(sortBySubcolumn, true);
    }
    this.sortingInfoChange.emit(sortInfo);
  }
}




@Directive({
  selector: '[gpf-table-cell-content]'
})
export class GpfTableCellContentDirective {
  templateRef: TemplateRef<any>;
  viewContainer: ViewContainerRef

  constructor(templateRef: TemplateRef<any>, viewContainer: ViewContainerRef) {    
    this.templateRef = templateRef;
    this.viewContainer = viewContainer;
  }
}

@Directive({
  selector: '[gpf-table-cell-header]'
})
export class GpfTableCellHeaderDirective {
  templateRef: TemplateRef<any>;
  viewContainer: ViewContainerRef

  constructor(templateRef: TemplateRef<any>, viewContainer: ViewContainerRef) {    
    this.templateRef = templateRef;
    this.viewContainer = viewContainer;
  }
}


class DefaultComparator {
  constructor(private subcolumn: GpfTableSubcolumnComponent) {   
  }

  compare(a: any, b: any): Number {
    let leftVal = a[this.subcolumn.field];
    let rightVal = b[this.subcolumn.field];
  
    if (leftVal == null && rightVal == null) return 0;
    if (leftVal == null) return -1;
    if (rightVal == null) return 1;
    
    if (!isNaN(leftVal) && !isNaN(rightVal)) {
      return +leftVal - +rightVal;
    }
    
    return leftVal.localeCompare(rightVal);
  }
}


@Component({
  selector: 'gpf-table-subcolumn',
  template: '',
})
export class GpfTableSubcolumnComponent {
  @ContentChildren(GpfTableCellContentDirective) contentChildren: QueryList<GpfTableCellContentDirective>;
  @ContentChildren(GpfTableCellHeaderDirective) headerChildren: QueryList<GpfTableCellHeaderDirective>;
  @Input() field: string;
  @Input() header: string;
  @Input() comparator: (leftVal: any, rightVal: any) => number = this.defaultComparator;

  contentTemplateRef: TemplateRef<any>;
  headerTemplateRef: TemplateRef<any>;

  constructor(protected viewContainer: ViewContainerRef) { 
  }

  ngAfterContentInit() {
    if (this.contentChildren.first) this.contentTemplateRef = this.contentChildren.first.templateRef;
    if (this.headerChildren.first) this.headerTemplateRef = this.headerChildren.first.templateRef;
  }
  
  defaultComparator(a: any, b: any): number {
    let leftVal = a[this.field];
    let rightVal = b[this.field];
  
    if (leftVal == null && rightVal == null) return 0;
    if (leftVal == null) return -1;
    if (rightVal == null) return 1;
    
    if (!isNaN(leftVal) && !isNaN(rightVal)) {
      return +leftVal - +rightVal;
    }
    
    return leftVal.localeCompare(rightVal);
  }
  
  sort(data: any, ascending: boolean) {
    data.sort((a, b) => {     
      if (ascending) {
        return this.comparator(a, b);
      }
      else {
        return this.comparator(b, a);       
      }
    });
  }
  
}


@Component({
  selector: 'gpf-table-column',
  template: '',
  entryComponents: [
    GpfTableHeader
  ]
})
export class GpfTableColumnComponent extends GpfTableSubcolumnComponent {
  @ContentChildren(GpfTableSubcolumnComponent) subcolumnsChildren: QueryList<GpfTableSubcolumnComponent>;

  constructor(viewContainer: ViewContainerRef) { 
    super(viewContainer);
  }

}

class SortInfo {
  constructor(public sortBySubcolumn: GpfTableSubcolumnComponent, public sortOrderAsc: boolean) { 
  }
}

@Component({
  selector: 'gpf-table',
  templateUrl: './table.component.html',
  styleUrls: ['./table.component.css']
})
export class GpfTableComponent {
  @ViewChild('table') viewChildDiv: any;
  @ContentChildren(GpfTableColumnComponent) columnsChildren: QueryList<GpfTableColumnComponent>;
  @Input() dataSource: any;
  private previousSortingInfo: SortInfo;
  
  @HostListener('window:scroll', ['$event']) 
  onWindowScroll(event) {
    //no-op, just run change detection
  }

  constructor(private viewContainer: ViewContainerRef, private ref: ChangeDetectorRef) { 
  }

  set sortingInfo(sortingInfo: SortInfo) {
    this.previousSortingInfo = sortingInfo;
    sortingInfo.sortBySubcolumn.sort(this.dataSource, sortingInfo.sortOrderAsc);
  }
  
  get sortingInfo(): SortInfo {
    return this.previousSortingInfo;
  }
  
  showFloatingHeader(): boolean {
    return this.viewChildDiv.nativeElement.getBoundingClientRect().top < 0;
  }
 
}
