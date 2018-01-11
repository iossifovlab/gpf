import { GeneSetsCollection, GeneSet } from './gene-sets';
import { IsNotEmpty } from 'class-validator';

export class GeneSetsState {
  geneSetsCollection: GeneSetsCollection;
  geneSetsTypes = new Set<any>();

  @IsNotEmpty()
  geneSet: GeneSet;
};
