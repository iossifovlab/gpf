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

    onClick() {
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
    }


    createUrl() {
        if (!this.urlUUID) {
            return '';
        }

        if (!this.url) {
            let pathname = this.router.createUrlTree(
                ["load-query", this.urlUUID]).toString();

            this.url = window.location.origin + pathname;
        }

        return this.url;
        
    }



}
