import { Dataset } from '../datasets/datasets';

export class DatasetNode {
  dataset: Dataset;
  children: DatasetNode[];

  constructor(dataset: Dataset, readonly allDatasets: readonly Dataset[]) {
    this.dataset = dataset;
    this.children = new Array<DatasetNode>();

    if (dataset.studies !== null) {
      allDatasets
        .filter(d => dataset.studies.indexOf(d.id) !== -1)
        .forEach(d => this.children.push(new DatasetNode(d, allDatasets)));
    }
  }
}