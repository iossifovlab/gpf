import { GeneSetsCollection, GeneSet } from './gene-sets';
import { IsNotEmpty } from 'class-validator';

export class GeneSetsLocalState {
  geneSetsCollection: GeneSetsCollection;
  geneSetsTypes = Object.create(null);

  @IsNotEmpty({message: 'Please select a gene set.'})
  geneSet: GeneSet;

  select(datasetId: string, personSetCollectionId: string, phenotype: string) {
    if (datasetId in this.geneSetsTypes && personSetCollectionId in this.geneSetsTypes[datasetId]) {
      this.geneSetsTypes[datasetId][personSetCollectionId].push(phenotype);
    } else {
      if (datasetId in this.geneSetsTypes) {
        Object.assign(this.geneSetsTypes[datasetId], { [personSetCollectionId]: [phenotype] });
      } else {
        Object.assign(this.geneSetsTypes, { [datasetId]: { [personSetCollectionId]: [phenotype] } });
      }
    }
  }

  deselect(datasetId: string, personSetCollectionId: string, phenotype: string) {
    if (datasetId in this.geneSetsTypes && personSetCollectionId in this.geneSetsTypes[datasetId]) {
      const index = this.geneSetsTypes[datasetId][personSetCollectionId].indexOf(phenotype);
      if (index > -1) {
        this.geneSetsTypes[datasetId][personSetCollectionId].splice(index, 1);
      }
    }
  }

  isSelected(datasetId: string, personSetCollectionId: string, phenotype: string): boolean {
    return datasetId in this.geneSetsTypes &&
        personSetCollectionId in this.geneSetsTypes[datasetId] &&
        this.geneSetsTypes[datasetId][personSetCollectionId].indexOf(phenotype) !== -1;
  }
}
