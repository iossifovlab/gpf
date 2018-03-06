import { UsersService } from '../users/users.service';
import { Component, OnInit, Input, Output, EventEmitter, NgZone } from '@angular/core';
import { DatasetsService } from './datasets.service';
import { Dataset } from './datasets';

import { IdName } from '../common/idname';
import { Observable } from 'rxjs';

import { ActivatedRoute, Params, Router } from '@angular/router';
import { Location } from '@angular/common';

@Component({
  selector: 'gpf-datasets',
  templateUrl: './datasets.component.html',
  styleUrls: ['./datasets.component.css'],

})
export class DatasetsComponent implements OnInit {
  registerAlertVisible = false;
  datasets$: Observable<Dataset[]>;
  selectedDataset$: Observable<Dataset>;
  @Output() selectedDatasetChange = new EventEmitter<Dataset>();

  constructor(
    private usersService: UsersService,
    private datasetsService: DatasetsService,
    private route: ActivatedRoute,
    private router: Router,
    private location: Location,
  ) {
  }

  ngOnInit() {
    console.log("datasets component init");
    this.route.params.subscribe(
      (params: Params) => {
        this.datasetsService.setSelectedDatasetById(params['dataset']);
      });

    this.datasets$ = this.datasetsService.getDatasetsObservable();
    this.selectedDataset$ = this.datasetsService.getSelectedDataset();

    this.datasets$
      .take(1)
      .subscribe(datasets => {
        if (!this.datasetsService.hasSelectedDataset()) {
          this.router.navigate(['/', 'datasets', datasets[0].id]);
        }
      });

    this.usersService.getUserInfoObservable()
      .subscribe(_ => {
        this.datasetsService.reloadSelectedDataset();
      });

    this.selectedDataset$
      .subscribe(selectedDataset => {
        if (!selectedDataset) {
          return;
        }
        this.registerAlertVisible = !selectedDataset.accessRights;
        if (selectedDataset.accessRights) {
          this.selectedDatasetChange.emit(selectedDataset);
        }
      });
  }

  selectDataset(dataset: Dataset) {
    if (dataset.description) {
      this.router.navigate(['/', 'datasets', dataset.id, 'description']);
    } else {
      this.router.navigate(['/', 'datasets', dataset.id]);
    }
  }
}
