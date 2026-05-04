import { Dataset } from '../datasets/datasets';

export class DatasetNode {
  public dataset: Dataset;
  public children: DatasetNode[];

  public constructor(dataset: Dataset, public readonly allDatasets: readonly Dataset[]) {
    this.dataset = dataset;
    this.children = new Array<DatasetNode>();

    allDatasets
      .filter(d => d.parents.indexOf(dataset.id) !== -1)
      .forEach(d => this.children.push(new DatasetNode(d, allDatasets)));
  }
}
