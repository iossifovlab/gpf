import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params, Router } from '@angular/router';

import { Observable } from 'rxjs';

import { DatasetsService } from '../datasets/datasets.service';
import { Dataset } from '../datasets/datasets';

@Component({
  selector: 'gpf-dataset-description',
  templateUrl: './dataset-description.component.html',
  styleUrls: ['./dataset-description.component.css']
})
export class DatasetDescriptionComponent implements OnInit {

  dataset$: Observable<Dataset>;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private datasetsService: DatasetsService,
  ) { }

  ngOnInit() {
    this.dataset$ = this.route.parent.params
      .map((params: Params) => params['dataset'])
      .filter(datasetId => !!datasetId)
      .switchMap(datasetId =>
        this.datasetsService.getDataset(datasetId));

    this.dataset$.take(1).subscribe(dataset => {
        if (!dataset.description) {
            this.router.navigate(['..', 'browser'], {
                relativeTo: this.route
            });
        }
    });
  }

}
