import { GeneSetsCollection, GeneSet } from './gene-sets';
import { IsNotEmpty } from 'class-validator';

export class GeneSetsState {
  geneSetsCollection: GeneSetsCollection;
  geneSetsTypes = Object.create(null);

  @IsNotEmpty()
  geneSet: GeneSet;

  select(datasetId: string, phenotype: string) {
    if (datasetId in this.geneSetsTypes) {
      this.geneSetsTypes[datasetId].push(phenotype);
    } else {
      Object.assign(this.geneSetsTypes, { [datasetId]: [phenotype] });
    }
  }

  deselect(datasetId: string, phenotype: string) {
    if (datasetId in this.geneSetsTypes) {
      let index = this.geneSetsTypes[datasetId].indexOf(phenotype);
      if (index > -1) {
        this.geneSetsTypes[datasetId].splice(index, 1);
      }
    }
  }

  isSelected(datasetId: string, phenotype: string) : boolean {
    return datasetId in this.geneSetsTypes &&
        this.geneSetsTypes[datasetId].indexOf(phenotype) != -1;
  }
};
