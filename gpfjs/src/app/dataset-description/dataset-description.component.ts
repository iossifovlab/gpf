import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { Observable } from 'rxjs';
import { DatasetsService } from '../datasets/datasets.service';
import { Dataset } from '../datasets/datasets';
import { filter, map, switchMap, take } from 'rxjs/operators';
import { EditorOption } from 'angular-markdown-editor';

@Component({
  selector: 'gpf-dataset-description',
  templateUrl: './dataset-description.component.html',
  styleUrls: ['./dataset-description.component.css']
})
export class DatasetDescriptionComponent implements OnInit {
  public dataset$: Observable<Dataset>;
  public datasetId: string;

  public editMode = false;
  public markdownText: string;
  public editorOptions: EditorOption = {
    autofocus: true,
    iconlibrary: 'fa',
    width: 700,
    resize: 'both',
    fullscreen: {enable: false, icons: undefined},
  };

  public constructor(
    private route: ActivatedRoute,
    private router: Router,
    private datasetsService: DatasetsService,
  ) { }

  public ngOnInit(): void {
    this.dataset$ = this.route.parent.params.pipe(
      map((params: Params) => params['dataset'] as string),
      filter(datasetId => Boolean(datasetId)),
      switchMap(datasetId => this.datasetsService.getDataset(datasetId))
    );

    this.dataset$.pipe(take(1)).subscribe(dataset => {
      this.datasetId = dataset.id;
      if (!dataset.description) {
        this.router.navigate(['..', 'browser'], {relativeTo: this.route});
      } else {
        this.markdownText = dataset.description;
      }
    });
  }

  public edit(): void {
    // check for admin rights
    this.editMode = true;
  }

  public save(): void {
    this.datasetsService.writeDatasetDescription(this.datasetId, this.markdownText).subscribe(() => {
      this.editMode = false;
    });
  }

  public close(): void {
    this.editMode = false;
    this.dataset$.pipe(take(1)).subscribe(dataset => {
      this.markdownText = dataset.description;
    });
  }
}
