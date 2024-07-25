import { Component, OnInit } from '@angular/core';
import { DatasetsService } from '../datasets/datasets.service';
import { switchMap, take } from 'rxjs/operators';
import { Store } from '@ngxs/store';
import { DatasetModel } from 'app/datasets/datasets.state';
import { DatasetHierarchy } from 'app/datasets/datasets';

@Component({
  selector: 'gpf-dataset-description',
  templateUrl: './dataset-description.component.html',
  styleUrls: ['./dataset-description.component.css']
})
export class DatasetDescriptionComponent implements OnInit {
  public descriptionHierarchy: DatasetHierarchy;
  public editable: boolean;


  public constructor(
    private datasetsService: DatasetsService,
    private store: Store
  ) { }

  public ngOnInit(): void {
    const subscription = this.store.selectOnce((state: { datasetState: DatasetModel}) => state.datasetState).pipe(
      switchMap((state: DatasetModel) => this.datasetsService.getDataset(state.selectedDatasetId)),
      switchMap(dataset => {
        this.editable = dataset.descriptionEditable;
        return this.datasetsService.getSingleDatasetHierarchy(dataset.id);
      }))
      .subscribe((hierarchy: DatasetHierarchy) => {
        this.addDescriptions(hierarchy);
        this.descriptionHierarchy = hierarchy;
        subscription.unsubscribe();
      });
  }

  public addDescriptions(hierarchy: DatasetHierarchy): void {
    const subscription = this.datasetsService.getDatasetDescription(hierarchy.id)
      .subscribe(desc => {
        hierarchy.description = desc;
        subscription.unsubscribe();
      });

    for (const child of hierarchy.children) {
      this.addDescriptions(child);
    }
  }

  public getFirstParagraph(text: string): string {
    const paragraphs = text.split('\n\n');

    let result = '';
    if (paragraphs[0].startsWith('#')) {
      const regexp = new RegExp(/^##((?:\n|.)*?)$\n/);
      if (regexp.test(paragraphs[0])) {
        result = paragraphs[0].replace(regexp, '');
      } else {
        result = paragraphs[1];
      }
    } else {
      result = paragraphs[0];
    }

    return result.replace('\n', ' ').trim();
  }

  public writeDataset(datasetId: string, text: string): void {
    this.datasetsService.writeDatasetDescription(datasetId, text).pipe(take(1)).subscribe();
  }
}
