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
