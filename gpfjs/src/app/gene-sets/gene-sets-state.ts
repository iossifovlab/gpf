import { GeneSetsCollection, GeneSet } from './gene-sets';
import { IsNotEmpty } from 'class-validator';

export class GeneSetsLocalState {
  geneSetsCollection: GeneSetsCollection;
  geneSetsTypes = Object.create(null);

  @IsNotEmpty()
  geneSet: GeneSet;

  select(datasetId: string, peopleGroupId: string, phenotype: string) {
    if (datasetId in this.geneSetsTypes && peopleGroupId in this.geneSetsTypes[datasetId]) {
      this.geneSetsTypes[datasetId][peopleGroupId].push(phenotype);
    } else {
      if (datasetId in this.geneSetsTypes) {
        Object.assign(this.geneSetsTypes[datasetId], { [peopleGroupId]: [phenotype] });
      } else {
        Object.assign(this.geneSetsTypes, { [datasetId]: { [peopleGroupId]: [phenotype] } });
      }
    }
  }

  deselect(datasetId: string, peopleGroupId: string, phenotype: string) {
    if (datasetId in this.geneSetsTypes && peopleGroupId in this.geneSetsTypes[datasetId]) {
      const index = this.geneSetsTypes[datasetId][peopleGroupId].indexOf(phenotype);
      if (index > -1) {
        this.geneSetsTypes[datasetId][peopleGroupId].splice(index, 1);
      }
    }
  }

  isSelected(datasetId: string, peopleGroupId: string, phenotype: string): boolean {
    return datasetId in this.geneSetsTypes &&
        peopleGroupId in this.geneSetsTypes[datasetId] &&
        this.geneSetsTypes[datasetId][peopleGroupId].indexOf(phenotype) !== -1;
  }
}
