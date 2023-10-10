import { Component, HostListener, OnInit } from '@angular/core';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { Observable } from 'rxjs';
import { DatasetsService } from '../datasets/datasets.service';
import { Dataset } from '../datasets/datasets';
import { filter, map, switchMap, take } from 'rxjs/operators';
import { EditorOption } from 'angular-markdown-editor';
import { MarkdownService } from 'ngx-markdown';
import DOMPurify from 'dompurify';
import { UsersService } from 'app/users/users.service';

@Component({
  selector: 'gpf-dataset-description',
  templateUrl: './dataset-description.component.html',
  styleUrls: ['./dataset-description.component.css']
})
export class DatasetDescriptionComponent implements OnInit {
  public dataset$: Observable<Dataset>;
  public datasetId: string;

  public loading = true;
  public editMode = false;
  public editorText: string;
  private initialDatasetDescription: string;
  public isDescriptionEditable: boolean;

  public editorOptions: EditorOption = {
    autofocus: true,
    iconlibrary: 'fa',
    width: 1105,
    resize: 'both',
    fullscreen: {enable: false, icons: undefined},
    parser: (val: string) => {
      const sanitizedText = DOMPurify.sanitize(val.trim());
      return this.markdownService.parse(sanitizedText);
    }
  };

  public constructor(
    private route: ActivatedRoute,
    private router: Router,
    private datasetsService: DatasetsService,
    private markdownService: MarkdownService,
    private usersService: UsersService
  ) { }

  @HostListener('keydown', ['$event']) public onKeyDown($event: KeyboardEvent): void {
    if ($event.ctrlKey && $event.code === 'Enter') {
      this.save();
    }
  }

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
      } else {
        this.editorText = dataset.description;
        this.initialDatasetDescription = dataset.description;
        this.isDescriptionEditable = dataset.descriptionEditable;
      }
      this.loading = false;
    });
  }

  public edit(): void {
    this.editMode = true;
  }

  public save(): void {
    this.loading = true;
    this.editMode = false;
    if (this.editorText !== this.initialDatasetDescription) {
      this.datasetsService.writeDatasetDescription(this.datasetId, this.editorText).subscribe(() => {
        this.ngOnInit();
      });
    }
  }

  public close(): void {
    this.editMode = false;
    if (this.editorText !== this.initialDatasetDescription) {
      this.dataset$.pipe(take(1)).subscribe(dataset => {
        this.editorText = dataset.description;
      });
    }
  }

  public togglePreview(): void {
    const previewButton = document.querySelector('[title="Preview"]');
    if (this.editorText.length !== 0) {
      previewButton.removeAttribute('disabled');
    } else {
      previewButton.setAttribute('disabled', '');
    }
  }

  public disablePreviewOnLoad(toDisable: boolean): void {
    if (toDisable) {
      const previewButton = document.querySelector('[title="Preview"]');
      previewButton.setAttribute('disabled', '');
    }
  }
}
