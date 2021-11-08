import { GenomicScore } from 'app/genotype-browser/genotype-browser';
import { Type } from 'class-transformer';

export class AgpConfig {
  defaultDataset: string;

  @Type(() => AgpGeneSetsCategory)
  geneSets: AgpGeneSetsCategory[];

  @Type(() => AgpGenomicScoresCategory)
  genomicScores: AgpGenomicScoresCategory[];

  @Type(() => AgpDataset)
  datasets: AgpDataset[];

  @Type(() => AgpOrder)
  order: AgpOrder[];
}

export class AgpGeneSetsCategory {
  category: string;
  displayName: string;
  defaultVisible: boolean;

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
  defaultVisible: boolean;

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

  @Type(() => AgpDatasetPersonSet)
  personSets: AgpDatasetPersonSet[];
}

export class AgpDatasetPersonSet {
  id: string;
  displayName: string;
  collectionId: string;
  description: string;
  parentsCount: number;
  childrenCount: number;
  
  @Type(() => AgpDatasetStatistic)
  statistics: AgpDatasetStatistic[];
}

export class AgpDatasetStatistic {
  id: string;
  displayName: string;
  effects: string[];
  category: string;
  description: string;
  variantTypes: string[];
  scores: GenomicScore[];
  defaultVisible: boolean;
}

export class AgpOrder {
  section: string;
  id: string;
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
