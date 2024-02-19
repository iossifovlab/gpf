import {
  Component, OnInit, AfterViewInit, Input, ComponentFactoryResolver,
  ViewChildren, ComponentFactory, ViewContainerRef, QueryList
} from '@angular/core';
import { PedigreeCounter } from '../variant-reports';
import {
  CommonReportsPedigreeCellComponent
} from '../common-reports-pedigree-cell/common-reports-pedigree-cell.component';

@Component({
  selector: '[gpf-common-reports-row]',
  templateUrl: './common-reports-row.component.html'
})
export class CommonReportsRowComponent implements OnInit, AfterViewInit {
  @Input() public pedigreeGroup: PedigreeCounter[];
  @ViewChildren('gpfPedigreeHost', {read: ViewContainerRef}) public gpfPedigreeHost: QueryList<ViewContainerRef>;

  private componentFactory: ComponentFactory<CommonReportsPedigreeCellComponent>;

  public constructor(
    private componentFactoryResolver: ComponentFactoryResolver
  ) { }

  public ngOnInit(): void {
    this.componentFactory = this.componentFactoryResolver.resolveComponentFactory(CommonReportsPedigreeCellComponent);
  }

  public ngAfterViewInit(): void {
    const hosts = this.gpfPedigreeHost.toArray();
    for (let i = 0; i < this.pedigreeGroup.length; i++) {
      setTimeout(() => {
        this.createPedigree(hosts[i], this.pedigreeGroup[i]);
      }, 1);
    }
  }

  private createPedigree(viewContainer: ViewContainerRef, pedigree: PedigreeCounter): void {
    const component = viewContainer.createComponent<CommonReportsPedigreeCellComponent>(this.componentFactory);
    component.instance.pedigree = pedigree;
  }
}
