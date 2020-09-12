import { Component, OnInit, Input, ComponentFactoryResolver, ViewChild, ComponentFactory, ViewContainerRef } from '@angular/core';
import { PedigreeCounter } from '../variant-reports';
import { CommonReportsPedigreeCellDirective } from '../common-reports-pedigree-cell.directive';
import { CommonReportsPedigreeCellComponent } from '../common-reports-pedigree-cell/common-reports-pedigree-cell.component';
import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';

@Component({
  selector: 'gpf-common-reports-row',
  templateUrl: './common-reports-row.component.html',
  styleUrls: ['./common-reports-row.component.css']
})
export class CommonReportsRowComponent implements OnInit {
  @Input() pedigreeGroup: [PedigreeData]

  @ViewChild(CommonReportsPedigreeCellDirective, {static: true}) pedigreeHost: CommonReportsPedigreeCellDirective;

  private componentFactory: ComponentFactory<CommonReportsPedigreeCellComponent>;
  private rowViewContainer: ViewContainerRef;

  constructor(private componentFactoryResolver: ComponentFactoryResolver) { }

  ngOnInit(): void {
    this.componentFactory = this.componentFactoryResolver.resolveComponentFactory(CommonReportsPedigreeCellComponent);

    this.rowViewContainer = this.pedigreeHost.viewContainerRef;
    for(let pedigree of this.pedigreeGroup) {
      setTimeout(() => {
        console.log(pedigree);
        this.createPedigree(pedigree);
      }, 1)
    }
  }

  async createPedigree(pedigree: PedigreeData): Promise<any> {
    const component = this.rowViewContainer.createComponent<CommonReportsPedigreeCellComponent>(this.componentFactory)
    component.instance.pedigree = pedigree;
  }

}
