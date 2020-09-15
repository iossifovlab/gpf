import { Component, OnInit, AfterViewInit, Input, ComponentFactoryResolver, ViewChild, ViewChildren, ComponentFactory, ViewContainerRef, QueryList } from '@angular/core';
import { PedigreeCounter } from '../variant-reports';
import { CommonReportsPedigreeCellComponent } from '../common-reports-pedigree-cell/common-reports-pedigree-cell.component';
import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';

@Component({
  selector: '[gpf-common-reports-row]',
  templateUrl: './common-reports-row.component.html',
  styleUrls: ['./common-reports-row.component.css']
})
export class CommonReportsRowComponent implements OnInit, AfterViewInit {
  @Input() pedigreeGroup: [PedigreeData];

  @ViewChildren("gpfPedigreeHost", {read: ViewContainerRef}) gpfPedigreeHost: QueryList<ViewContainerRef>;

  private componentFactory: ComponentFactory<CommonReportsPedigreeCellComponent>;

  constructor(private componentFactoryResolver: ComponentFactoryResolver) { }

  ngOnInit(): void {
    this.componentFactory = this.componentFactoryResolver.resolveComponentFactory(CommonReportsPedigreeCellComponent);
  }

  ngAfterViewInit() {
    const hosts = this.gpfPedigreeHost.toArray();
    for(let i = 0; i < this.pedigreeGroup.length; i++) {
      setTimeout(() => {
        this.createPedigree(hosts[i], this.pedigreeGroup[i]);
      }, 1);
    }
  }

  async createPedigree(viewContainer: ViewContainerRef, pedigree: PedigreeData): Promise<any> {
    const component = viewContainer.createComponent<CommonReportsPedigreeCellComponent>(this.componentFactory);
    component.instance.pedigree = pedigree;
  }
}
