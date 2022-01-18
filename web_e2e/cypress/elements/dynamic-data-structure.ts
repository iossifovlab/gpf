import { Type } from 'class-transformer';


export class EnrichmentToolData {
  name: string;
  study: string;
  target: string;

  @Type(() => Case)
  cases: Case[];
}

class Case {
  name: string;

  @Type(() => Params)
  params: Params;

  @Type(() => Expected)
  expected: Expected[];
}

class Expected {
  rowId: string;
  values: string[];
}

export class Params {
  geneSymbols: string[];

  @Type(() => Models)
  models: Models;

  @Type(() => GeneWeight)
  geneWeight: GeneWeight;

  @Type(() => GeneSet)
  geneSet: GeneSet;
}

class Models {
  backgroundModel: string;
  countingModel: string;
}

class GeneWeight {
  id: string;
  from: number;
  to: number;
}

class GeneSet {
  id: string

  @Type(() => GeneSetCollection)
  collection: GeneSetCollection;
}

class GeneSetCollection {
  id: string;

  @Type(() => GeneSetCollectionAffectedStatus)
  affectedStatus: GeneSetCollectionAffectedStatus[];
}

class GeneSetCollectionAffectedStatus {
  studyId: string;
  affected: boolean;
  unaffected: boolean
}