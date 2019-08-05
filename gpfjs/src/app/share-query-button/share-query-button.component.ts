import { Component, OnInit, Input, ViewChild } from '@angular/core';
import { QueryStateCollector } from '../query/query-state-provider';
import { DatasetsService } from '../datasets/datasets.service';
import { QueryService } from '../query/query.service';
import { NgbDropdown } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-share-query-button',
  templateUrl: './share-query-button.component.html',
  styleUrls: ['./share-query-button.component.css']
})
export class ShareQueryButtonComponent implements OnInit {

  @Input()
  queryType: string;

  @ViewChild(NgbDropdown)
  dropdown: NgbDropdown;


  private urlUUID: string;
  private url: string;
  private savedUrlUUID: string;
  buttonValue = 'Copy';

  constructor(
    private datasetsService: DatasetsService,
    private queryService: QueryService,
    // should be provided by a parent component..
    private parentComponent: QueryStateCollector
  ) { }

  ngOnInit() {
  }

    saveIfOpened(opened: boolean) {
      if (opened) {
        this.buttonValue = 'Copy';
        this.parentComponent.getCurrentState()
          .take(1)
          .subscribe(state => {
              this.queryService.saveQuery(state, this.queryType)
                  .take(1)
                  .subscribe(response => {
                      this.urlUUID = response['uuid'];
                  });
          },
          error => {
            this.resetState();
            this.dropdown.close();
          });
      } else {
        this.resetState();
      }

    }

    private resetState() {
        this.savedUrlUUID = null;
        this.url = null;
    }

    createUrl() {
        if (!this.urlUUID) {
            return '';
        }

        if (this.savedUrlUUID !== this.urlUUID) {
            this.url = this.queryService.getLoadUrl(this.urlUUID);
            this.savedUrlUUID = this.urlUUID;
        }

        return this.url;

    }

    copyToClipboard(input) {
      input.select();
      document.execCommand('Copy');
      this.buttonValue = 'Copied';
    }

}
