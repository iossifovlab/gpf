import { Component, OnInit, Input, ViewChild } from '@angular/core';
import { QueryService } from '../query/query.service';
import { DatasetsService } from '../datasets/datasets.service';
import { Store } from '@ngxs/store';
import { NgbDropdown } from '@ng-bootstrap/ng-bootstrap';
import { take } from 'rxjs/operators';

@Component({
  selector: 'gpf-share-query-button',
  templateUrl: './share-query-button.component.html',
  styleUrls: ['./share-query-button.component.css']
})
export class ShareQueryButtonComponent {
  @Input() queryType: string;
  @Input() disabled: boolean;
  @ViewChild(NgbDropdown)
  dropdown: NgbDropdown;

  private urlUUID: string;
  public url: string;
  private savedUrlUUID: string;
  buttonValue = 'Copy';

  constructor(
    private store: Store,
    private queryService: QueryService,
    private datasetsService: DatasetsService,
  ) { }

  public saveIfOpened(opened: boolean): void {
    if (!opened) {
      this.resetState();
      return;
    }

    const datasetId = this.datasetsService.getSelectedDataset().id;
    this.buttonValue = 'Copy';
    this.store.selectOnce(state => state).subscribe(state => {
      state['datasetId'] = datasetId;
      this.queryService.saveQuery(state, this.queryType)
        .pipe(take(1))
        .subscribe(response => {
          this.urlUUID = response['uuid'];
          this.setUrl();
        });
      },
      error => {
        this.resetState();
        this.dropdown.close();
      }
    );
  }

  private resetState() {
    this.savedUrlUUID = null;
    this.url = null;
  }

  private setUrl(): void {
    if (!this.urlUUID) {
      return;
    }

    if (this.savedUrlUUID !== this.urlUUID) {
      this.url = this.queryService.getLoadUrl(this.urlUUID);
      this.savedUrlUUID = this.urlUUID;
    }
  }

  public copyToClipboard(inputElement): void {
    inputElement.select();
    document.execCommand('Copy');
    this.buttonValue = 'Copied';
  }
}
