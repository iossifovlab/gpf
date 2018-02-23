import { Component, OnInit, Input, Output, EventEmitter, Host } from '@angular/core';
import { Location } from '@angular/common';
import { Router } from '@angular/router';
import { QueryStateCollector } from '../query/query-state-provider';
import { DatasetsService } from '../datasets/datasets.service';
import { SaveQuery } from '../query/common-query-data';
import { GenotypeBrowserComponent } from '../genotype-browser/genotype-browser.component';
import { SaveQueryService } from './save-query.service';


@Component({
  selector: 'gpf-save-query-button',
  templateUrl: './save-query-button.component.html',
  styleUrls: ['./save-query-button.component.css']
})
export class SaveQueryButtonComponent implements OnInit {

  @Input()
  queryType: string;

  private urlUUID: string;
  private url: string;
  private savedUrlUUID: string;
  buttonValue = "Copy";

  constructor(
  	private datasetsService: DatasetsService,
    private saveQueryService: SaveQueryService,
    private router: Router,
    private location: Location,
    // should be provided by a parent component..
  	private parentComponent: QueryStateCollector 

  ) { }

  ngOnInit() {
  }

    saveIfOpened(opened: boolean) {
      if(opened) {
        this.buttonValue = "Copy";
        this.parentComponent.getCurrentState()
          .take(1)
          .subscribe(state => {
              this.saveQueryService.saveQuery(state, this.queryType)
                  .take(1)
                  .subscribe(response => {
                      this.urlUUID = response["uuid"];
                  });
          },
          error => {
          });
      } else {
        this.savedUrlUUID = null;
        this.url = null;
      }
      
    }


    createUrl() {
        if (!this.urlUUID) {
            return '';
        }

        if (this.savedUrlUUID != this.urlUUID) {
            let pathname = this.router.createUrlTree(
                ["load-query", this.urlUUID]).toString();

            this.url = window.location.origin + pathname;
            this.savedUrlUUID = this.urlUUID;
        }

        return this.url;
        
    }

    copyToClipboard(input) {
      input.select()
      document.execCommand("Copy");
      this.buttonValue = "Copied";
    }

}
