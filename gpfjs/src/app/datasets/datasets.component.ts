import { UsersService } from '../users/users.service';
import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { DatasetsService } from './datasets.service';
import { Dataset } from './datasets';

// tslint:disable-next-line:import-blacklist
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
  ) { }

  ngOnInit() {
    this.route.params.subscribe(
      (params: Params) => {
        this.datasetsService.setSelectedDatasetById(params['dataset']);
      });

    this.datasets$ = this.filterHiddenGroups(
      this.datasetsService.getDatasetsObservable());

    this.selectedDataset$ = this.datasetsService.getSelectedDataset();

    this.datasets$
      .take(1)
      .subscribe(datasets => {
        if (!this.datasetsService.hasSelectedDataset()) {
          this.selectDataset(datasets[0]);
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

  findFirstTool(selectedDataset: Dataset) {
    if (selectedDataset.description) {
      return 'description';
    } else if (selectedDataset.genotypeBrowser && selectedDataset.genotypeBrowserConfig) {
      return 'browser';
    } else if (selectedDataset.phenotypeBrowser) {
      return 'phenotypeBrowser';
    } else if (selectedDataset.enrichmentTool) {
      return 'enrichment';
    } else if (selectedDataset.phenotypeGenotypeTool) {
      return 'phenoTool';
    } else if (selectedDataset) {
      return 'commonReport';
    } else {
      return '';
    }
  }

  filterHiddenGroups(datasets: Observable<Dataset[]>): Observable<Dataset[]> {
    return datasets.map(datasets =>
      datasets.filter(dataset =>
        dataset.groups.find(g => g.name === 'hidden') == null || dataset.accessRights));
  }

  selectDataset(dataset: Dataset) {
    this.router.navigate(['/', 'datasets', dataset.id, this.findFirstTool(dataset)]);
  }
}
