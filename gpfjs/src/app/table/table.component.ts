import { Input, Directive, Component, OnInit, ContentChildren, QueryList, TemplateRef, ViewContainerRef, ComponentFactoryResolver } from '@angular/core';


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
  selector: 'gpf-table-header',
  templateUrl: './table-header.component.html'
})
export class GpfTableHeader {
  @Input() subcolumnsChildren: QueryList<GpfTableSubcolumnComponent>;
  @Input() headerTemplateRef: TemplateRef<any>;

  constructor(private viewContainer: ViewContainerRef) { 
    this.viewContainer = viewContainer;
  }
}

@Component({
  selector: 'gpf-table-cell',
  templateUrl: './table-cell.component.html'
})
export class GpfTableCell {
  @Input() subcolumnsChildren: QueryList<GpfTableSubcolumnComponent>;
  @Input() data: any;

  constructor(private viewContainer: ViewContainerRef) { 
    this.viewContainer = viewContainer;
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

  ngOnInit() {

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
export class GpfTableSubcolumnComponent implements OnInit {
  @ContentChildren(GpfTableCellContentDirective) contentChildren: QueryList<GpfTableCellContentDirective>;
  @ContentChildren(GpfTableCellHeaderDirective) headerChildren: QueryList<GpfTableCellHeaderDirective>;

  contentTemplateRef: TemplateRef<any>;
  headerTemplateRef: TemplateRef<any>;

  constructor(private viewContainer: ViewContainerRef) { 
  }

  ngOnInit() {
   
  }
  
  ngAfterContentInit() {
    this.contentTemplateRef = this.contentChildren.first.templateRef;
    this.headerTemplateRef = this.headerChildren.first.templateRef;
  }
  
  ngAfterViewInit() {
  }
}


@Component({
  selector: 'gpf-table-column',
  template: '',
  entryComponents: [
    GpfTableHeader
  ]
})
export class GpfTableColumnComponent {
  @ContentChildren(GpfTableSubcolumnComponent) subcolumnsChildren: QueryList<GpfTableSubcolumnComponent>;
  @ContentChildren(GpfTableCellContentDirective) contentChildren: QueryList<GpfTableCellContentDirective>;
  @ContentChildren(GpfTableCellHeaderDirective) headerChildren: QueryList<GpfTableCellHeaderDirective>;

  constructor() { 
  }

}



@Component({
  selector: 'gpf-table',
  templateUrl: './table.component.html',
  styleUrls: ['./table.component.css']
})
export class GpfTableComponent implements OnInit {
  @ContentChildren(GpfTableColumnComponent) columnsChildren: QueryList<GpfTableColumnComponent>;
  @Input() dataSource: any;

  constructor(private viewContainer: ViewContainerRef) { 
  }

  ngOnInit() {

  }
}
