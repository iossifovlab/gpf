import { OnInit, Component, HostListener, Input } from '@angular/core';

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
export class PhenoBrowserTableComponent implements OnInit {
  @Input() public measures: PhenoMeasures;

  public singleColumnWidth;
  private columnsCount = 8;

  public constructor(
    private modalService: NgbModal
  ) { }

  public ngOnInit(): void {
    this.onResize();
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
