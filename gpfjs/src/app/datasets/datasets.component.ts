import { UsersService } from '../users/users.service';
import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
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

  selectedDatasetId: string;

  constructor(
    private usersService: UsersService,
    private datasetsService: DatasetsService,
    private route: ActivatedRoute,
    private router: Router,
    private location: Location
  ) {
  }

  ngOnInit() {
    this.route.params.subscribe(
      (params: Params) => {
        this.datasetsService.setSelectedDatasetById(params['dataset']);
      }
    );

    this.datasets$ = this.datasetsService.getDatasetsObservable();
    this.selectedDataset$ = this.datasetsService.getSelectedDataset();

    this.usersService.getUserInfo()
      .switchMap(_ => this.datasetsService.getDatasets())
      .take(1)
      .subscribe(datasets => {
        if (!this.datasetsService.hasSelectedDataset()) {
          this.datasetsService.setSelectedDataset(datasets[0]);
        }
      });

    this.selectedDataset$.subscribe(selectedDataset => {
      if (!selectedDataset) {
        return;
      }

      this.router.navigate([selectedDataset.id], { relativeTo: this.route });
      this.registerAlertVisible = !selectedDataset.accessRights;
      if (selectedDataset.accessRights) {
        this.selectedDatasetChange.emit(selectedDataset);
      }
    });
  }
}
