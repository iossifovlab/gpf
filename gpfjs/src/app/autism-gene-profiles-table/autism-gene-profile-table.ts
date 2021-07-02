import { Type } from 'class-transformer';

export class AgpConfig {
  defaultDataset: string;

  @Type(() => AgpGeneSetsCategory)
  geneSets: AgpGeneSetsCategory[];

  @Type(() => AgpGenomicScoresCategory)
  genomicScores: AgpGenomicScoresCategory[];

  @Type(() => AgpDataset)
  datasets: AgpDataset[];
}

export class AgpGeneSetsCategory {
  category: string;
  displayName: string;

  @Type(() => AgpGeneSet)
  sets: AgpGeneSet[];
}

export class AgpGeneSet {
  setId: string;
  collectionId: string;
  meta: string;
  defaultVisible: boolean;
}

export class AgpGenomicScoresCategory {
  category: string;
  displayName: string;

  @Type(() => AgpGenomicScore)
  scores: AgpGenomicScore[];
}

export class AgpGenomicScore {
  scoreName: string;
  format: string;
  meta: string;
  defaultVisible: boolean;
}

export class AgpDataset {
  id: string;
  displayName: string;
  meta: string;
  defaultVisible: boolean;

  @Type(() => AgpDatasetStatistic)
  statistics: AgpDatasetStatistic[];

  @Type(() => AgpDatasetPersonSet)
  personSets: AgpDatasetPersonSet[];
}

export class AgpDatasetStatistic {
  id: string;
  displayName: string;
  effects: string[];
  category: string;
  description: string;
  variantTypes: string[];
}

export class AgpDatasetPersonSet {
  id: string;
  displayName: string;
  description: string;
  parentsCount: number;
  childrenCount: number;
}

export class AgpTableConfig {
  constructor(
    public defaultDataset: string,
    public geneSets: AgpTableGeneSetsCategory[],
    public genomicScores: AgpTableGenomicScoresCategory[],
    public datasets: AgpTableDataset[]
  ) {}
}

export class AgpTableGeneSetsCategory {
  constructor(
    public category: string,
    public displayName: string,
    public sets: AgpTableGeneSet[]
  ) {}
}

export class AgpTableGeneSet {
  constructor(
    public setId: string,
    public collectionId: string,
    public meta: string,
    public defaultVisible: boolean
  ) {}
}

export class AgpTableGenomicScoresCategory {
  constructor(
    public category: string,
    public displayName: string,
    public scores: AgpTableGenomicScore[]
  ) {}
}

export class AgpTableGenomicScore {
  constructor(
    public scoreName: string,
    public format: string,
    public meta: string,
    public defaultVisible: boolean
  ) {}
}

export class AgpTableDataset {
  constructor(
    public id: string,
    public displayName: string,
    public meta: string,
    public defaultVisible: boolean,
    public personSets: AgpTableDatasetPersonSet[]
  ) {}
}

export class AgpTableDatasetPersonSet {
  constructor(
    public id: string,
    public displayName: string,
    public description: string,
    public parentsCount: number,
    public childrenCount: number,
    public statistics: AgpTableDatasetStatistic[]
  ) {}
}

export class AgpTableDatasetStatistic {
  constructor(
    public id: string,
    public displayName: string,
    public effects: string[],
    public category: string,
    public description: string,
    public variantTypes: string[]
  ) {}
}

export class AgpGene {
  geneSymbol: string;
  geneSets: string[];

  @Type(() => AgpGenomicScores)
  genomicScores: AgpGenomicScores[];

  @Type(() => AgpStudy)
  studies: AgpStudy[];
}

export class AgpGenomicScores {
  id: string;

  @Type(() => AgpGenomicScoreWithValue)
  scores: AgpGenomicScoreWithValue[];
}

export class AgpGenomicScoreWithValue {
  id: string;
  value: number;
  format: string;
}

export class AgpStudy {
  id: string;

  @Type(() => AgpPersonSet)
  personSets: AgpPersonSet[];
}

export class AgpPersonSet {
  id: string;

  @Type(() => AgpEffectType)
  effectTypes: AgpEffectType[];
}

export class AgpEffectType {
  id: string;
  value: number;
}
