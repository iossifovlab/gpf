import { ChangeDetectorRef, Output, EventEmitter, Input, Directive, Component, OnInit, ContentChildren, QueryList, TemplateRef, ViewContainerRef, ComponentFactoryResolver } from '@angular/core';


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
  @Output() sortingFieldChange = new EventEmitter();

  constructor(private viewContainer: ViewContainerRef) { 
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



@Component({
  selector: 'gpf-table-subcolumn',
  template: '',
})
export class GpfTableSubcolumnComponent {
  @ContentChildren(GpfTableCellContentDirective) contentChildren: QueryList<GpfTableCellContentDirective>;
  @ContentChildren(GpfTableCellHeaderDirective) headerChildren: QueryList<GpfTableCellHeaderDirective>;
  @Input() field: string;
  @Input() header: string;

  contentTemplateRef: TemplateRef<any>;
  headerTemplateRef: TemplateRef<any>;

  constructor(protected viewContainer: ViewContainerRef) { 
  }

  ngAfterContentInit() {
    if (this.contentChildren.first) this.contentTemplateRef = this.contentChildren.first.templateRef;
    if (this.headerChildren.first) this.headerTemplateRef = this.headerChildren.first.templateRef;
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



@Component({
  selector: 'gpf-table',
  templateUrl: './table.component.html',
  styleUrls: ['./table.component.css']
})
export class GpfTableComponent {
  @ContentChildren(GpfTableColumnComponent) columnsChildren: QueryList<GpfTableColumnComponent>;
  @Input() dataSource: any;

  constructor(private viewContainer: ViewContainerRef, private ref: ChangeDetectorRef) { 
  }

 
  sort(field: string) {
    this.dataSource.sort((a, b) => {
      let leftVal = a[field];
      let rightVal = b[field];
    
      if (leftVal == null && rightVal == null) return 0;
      if (leftVal == null) return -1;
      if (rightVal == null) return 1;
      
      if (!isNaN(leftVal) && !isNaN(rightVal)) {
        return +leftVal - +rightVal;
      }
      
      return leftVal.localeCompare(rightVal);
    });
    console.log(this.dataSource);
  }
}
