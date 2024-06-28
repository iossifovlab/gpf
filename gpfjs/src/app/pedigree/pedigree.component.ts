import { Component, Input, ViewChild } from '@angular/core';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { Store } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { DatasetModel } from 'app/datasets/datasets.state';
import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';
import { VariantReportsService } from 'app/variant-reports/variant-reports.service';
import { switchMap } from 'rxjs';

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
  @ViewChild('pedigreeModal') public pedigreeModal;
  public modal: NgbModalRef;
  public familyIdsList: string[];
  public pedigreeScale = 2.5;
  public selectedDatasetId = '';

  public constructor(
    public modalService: NgbModal,
    private variantReportsService: VariantReportsService,
    public configService: ConfigService,
    private store: Store
  ) { }

  public loadFamilyListData(): void {
    if (this.familyIdsList !== undefined) {
      return;
    }

    this.store.selectOnce((state: { datasetState: DatasetModel}) => state.datasetState).pipe(
      switchMap((state: DatasetModel) => {
        this.selectedDatasetId = state.selectedDataset.id;
        return this.variantReportsService.getFamilies(
          this.selectedDatasetId,
          this.groupName,
          this.counterId
        );
      })).subscribe(list => {
      this.familyIdsList = list;
    });
  }

  public openModal(): void {
    if (this.modalService.hasOpenModals()) {
      return;
    }
    if (!this.modalSimpleView) {
      this.loadFamilyListData();
    }
    this.modal = this.modalService.open(
      this.pedigreeModal,
      {animation: false, centered: true, size: 'lg', windowClass: 'pedigree-modal'}
    );
  }

  public closeModal(): void {
    this.modal.close();
  }

  public getDownloadLink(): string {
    return this.variantReportsService.getDownloadLink() + this.selectedDatasetId;
  }

  public onSubmit(event): void {
    this.store.selectOnce((state: { datasetState: DatasetModel}) => state.datasetState).subscribe(state => {
      const selectedDatasetId = state.selectedDataset.id;
      const args = {
        study_id: selectedDatasetId,
        group_name: this.groupName,
        counter_id: this.counterId
      };
      event.target.queryData.value = JSON.stringify(args);
      event.target.submit();
    });
  }
}
