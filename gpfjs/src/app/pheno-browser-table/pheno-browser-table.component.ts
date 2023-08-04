import {
  OnInit, Component, HostListener, Input, OnChanges, TemplateRef, ViewContainerRef, ViewChild
} from '@angular/core';

import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import {
  PhenoBrowserModalContentComponent
} from '../pheno-browser-modal-content/pheno-browser-modal-content.component';
import { PhenoMeasures } from '../pheno-browser/pheno-browser';

@Component({
  selector: 'gpf-pheno-browser-table',
  templateUrl: './pheno-browser-table.component.html',
  styleUrls: ['./pheno-browser-table.component.css']
})
export class PhenoBrowserTableComponent implements OnInit, OnChanges {
  @Input() public measures: PhenoMeasures;
  @ViewChild('templateRef', { read: TemplateRef }) private templateRef: TemplateRef<Element>;
  @ViewChild('viewContainerRef', { read: ViewContainerRef }) private viewContainerRef: ViewContainerRef;

  public singleColumnWidth;
  private columnsCount = 8;

  public constructor(
    private modalService: NgbModal
  ) { }

  public ngOnInit(): void {
    this.onResize();
  }

  public ngOnChanges(): void {
    this.viewContainerRef?.clear();
    this.viewContainerRef?.createEmbeddedView(this.templateRef);
  }

  public static compare(leftVal: any, rightVal: any): number {
    if (leftVal === null && rightVal === null) {
      return 0;
    }
    if (leftVal === null) {
      return -1;
    }
    if (rightVal === null) {
      return 1;
    }

    if (!isNaN(leftVal) && !isNaN(rightVal)) {
      return Number(leftVal) - Number(rightVal);
    }

    return leftVal.localeCompare(rightVal);
  }

  @HostListener('window:resize', ['$event'])
  public onResize(): void {
    const screenWidth = window.innerWidth;
    const padding = 60;
    const scrollSize = 15;

    this.singleColumnWidth = `${(screenWidth - padding - scrollSize) / this.columnsCount}px`;
  }

  public openModal(imageUrl: string): void {
    if (imageUrl) {
      const modalRef = this.modalService.open(PhenoBrowserModalContentComponent, {
        windowClass: 'modal-fullscreen'
      });
      modalRef.componentInstance.imageUrl = imageUrl;
    }
  }
}
