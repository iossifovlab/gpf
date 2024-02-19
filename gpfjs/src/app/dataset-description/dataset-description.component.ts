import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { Observable } from 'rxjs';
import { DatasetsService } from '../datasets/datasets.service';
import { Dataset } from '../datasets/datasets';
import { filter, map, switchMap, take } from 'rxjs/operators';
import { UsersService } from 'app/users/users.service';

@Component({
  selector: 'gpf-dataset-description',
  templateUrl: './dataset-description.component.html'
})
export class DatasetDescriptionComponent implements OnInit {
  public dataset$: Observable<Dataset>;
  public datasetId: string;

  public constructor(
    private route: ActivatedRoute,
    private router: Router,
    private datasetsService: DatasetsService,
    private usersService: UsersService
  ) { }

  public ngOnInit(): void {
    this.dataset$ = this.route.parent.params.pipe(
      map((params: Params) => params['dataset'] as string),
      filter(datasetId => Boolean(datasetId)),
      switchMap(datasetId => this.datasetsService.getDataset(datasetId))
    );

    this.dataset$.pipe(take(1)).subscribe(dataset => {
      this.datasetId = dataset.id;
      if (!dataset.description && !this.usersService.cachedUserInfo().isAdministrator) {
        this.router.navigate(['..', 'browser'], {relativeTo: this.route});
      }
    });
  }

  public writeDataset(markdown: string): void {
    this.datasetsService.writeDatasetDescription(this.datasetId, markdown).pipe(take(1)).subscribe();
  }
}
