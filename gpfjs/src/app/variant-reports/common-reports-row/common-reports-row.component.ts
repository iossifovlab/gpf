import { Component, OnInit, AfterContentInit, Input, ComponentFactoryResolver, ViewChild, ContentChildren, ComponentFactory, ViewContainerRef, QueryList } from '@angular/core';
import { PedigreeCounter } from '../variant-reports';
import { CommonReportsPedigreeCellDirective } from '../common-reports-pedigree-cell.directive';
import { CommonReportsPedigreeCellComponent } from '../common-reports-pedigree-cell/common-reports-pedigree-cell.component';
import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';

@Component({
  selector: '[gpf-common-reports-row]',
  templateUrl: './common-reports-row.component.html',
  styleUrls: ['./common-reports-row.component.css']
})
export class CommonReportsRowComponent implements OnInit, AfterContentInit {
  @Input() pedigreeGroup: [PedigreeData];

  @ContentChildren(CommonReportsPedigreeCellDirective, { descendants: true }) gpfPedigreeHost: QueryList<CommonReportsPedigreeCellDirective>;

  private componentFactory: ComponentFactory<CommonReportsPedigreeCellComponent>;
  // private rowViewContainer: ViewContainerRef;

  constructor(private componentFactoryResolver: ComponentFactoryResolver) { }

  ngOnInit(): void {
    this.componentFactory = this.componentFactoryResolver.resolveComponentFactory(CommonReportsPedigreeCellComponent);

    // this.rowViewContainer = this.gpfPedigreeHost.viewContainerRef;

    for(let i = 0; i < this.pedigreeGroup.length; i++) {
      // console.log(i);
      // setTimeout(() => {
      //   this.createPedigree(this.rowViewContainer, pedigree);
      // }, 1);
    }

    // for (const pedigree of this.pedigreeGroup) {
    //   setTimeout(() => {
    //     console.log(pedigree);
    //     this.createPedigree(this.rowViewContainer, pedigree);
    //   }, 1);
    // }
  }

  ngAfterContentInit() {
    console.log(this.gpfPedigreeHost);
    this.gpfPedigreeHost.changes.subscribe(c => console.log(this.gpfPedigreeHost.toArray()));
  }

  async createPedigree(viewContainer: ViewContainerRef, pedigree: PedigreeData): Promise<any> {
    const component = viewContainer.createComponent<CommonReportsPedigreeCellComponent>(this.componentFactory);
    component.instance.pedigree = pedigree;
  }
}
