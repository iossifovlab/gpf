import { Component, Input, ViewChild } from '@angular/core';
import { PedigreeComponent } from 'app/pedigree/pedigree.component';
import { PedigreeCounter } from '../variant-reports';

@Component({
  selector: 'gpf-common-reports-pedigree-cell',
  templateUrl: './common-reports-pedigree-cell.component.html',
  styleUrls: ['./common-reports-pedigree-cell.component.css']
})
export class CommonReportsPedigreeCellComponent {
  @Input() public pedigree: PedigreeCounter;
  @Input() public modalSimpleView = false;
  @ViewChild(PedigreeComponent) public pedigreeComponent: PedigreeComponent;
  public pedigreeMaxWidth = 300;

  public openModal(): void {
    this.pedigreeComponent.openModal();
  }
}
