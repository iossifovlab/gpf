import { Component, Input } from '@angular/core';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';
import { VariantReportsService } from 'app/variant-reports/variant-reports.service';

@Component({
  selector: 'gpf-pedigree',
  templateUrl: './pedigree.component.html',
  styleUrls: ['./pedigree.component.css']
})
export class PedigreeComponent {
  @Input() public family: PedigreeData[];
  @Input() public groupName: string;
  @Input() public counterId: number;
  @Input() public pedigreeMaxWidth: number;
  @Input() public pedigreeMaxHeight: number;

  @Input() public modalSimpleView = true;
  public modal: NgbModalRef;
  public familyIdsList: string[];
  public pedigreeScale = 2.5;

  public constructor(
    public modalService: NgbModal,
    private variantReportsService: VariantReportsService,
    private datasetsService: DatasetsService,
    public configService: ConfigService,
  ) { }

  public loadFamilyListData(): void {
    if (this.familyIdsList !== undefined) {
      return;
    }

    this.variantReportsService.getFamilies(
      this.datasetsService.getSelectedDataset().id,
      this.groupName,
      this.counterId
    ).subscribe(list => {
      this.familyIdsList = list;
    });
  }

  public openModal(pedigreeModal): void {
    this.loadFamilyListData();
    this.modal = this.modalService.open(
      pedigreeModal,
      {animation: false, centered: true, size: 'lg', windowClass: 'pedigree-modal'}
    );
  }

  public closeModal(): void {
    this.modal.close();
  }

  public onSubmit(event): void {
    event.target.queryData.value = JSON.stringify({
      study_id: this.datasetsService.getSelectedDataset().id,
      group_name: this.groupName,
      counter_id: this.counterId
    });
    event.target.submit();
  }
}
