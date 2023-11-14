import { GenomicScore } from 'app/genotype-browser/genotype-browser';
import { Type } from 'class-transformer';

export class AgpSingleViewConfig {
  public shown: Array<{category: any; section: string; id: string}>;
  public defaultDataset: string;

  @Type(() => AgpGeneSetsCategory)
  public geneSets: AgpGeneSetsCategory[];

  @Type(() => AgpGenomicScoresCategory)
  public genomicScores: AgpGenomicScoresCategory[];

  @Type(() => AgpDataset)
  public datasets: AgpDataset[];

  @Type(() => AgpOrder)
  public order: AgpOrder[];

  public pageSize: number;
}

export class AgpGeneSetsCategory {
  public category: string;
  public displayName: string;
  public defaultVisible: boolean;

  @Type(() => AgpGeneSet)
  public sets: AgpGeneSet[];
}

export class AgpGeneSet {
  public setId: string;
  public collectionId: string;
  public meta: string;
  public defaultVisible: boolean;
}

export class AgpGenomicScoresCategory {
  public category: string;
  public displayName: string;
  public defaultVisible: boolean;

  @Type(() => AgpGenomicScore)
  public scores: AgpGenomicScore[];
}

export class AgpGenomicScore {
  public scoreName: string;
  public format: string;
  public meta: string;
  public defaultVisible: boolean;
}

export class AgpDataset {
  public id: string;
  public displayName: string;
  public meta: string;
  public defaultVisible: boolean;

  public shown: AgpDatasetPersonSet[];
  public statistics: AgpDatasetStatistic[];

  @Type(() => AgpDatasetPersonSet)
  public personSets: AgpDatasetPersonSet[];
}

export class AgpDatasetPersonSet {
  public id: string;
  public displayName: string;
  public collectionId: string;
  public description: string;
  public parentsCount: number;
  public childrenCount: number;
  public defaultVisible = true;

  public shown: AgpDatasetStatistic[];

  @Type(() => AgpDatasetStatistic)
  public statistics: AgpDatasetStatistic[];
}

export class AgpDatasetStatistic {
  public id: string;
  public displayName: string;
  public effects: string[];
  public category: string;
  public description: string;
  public variantTypes: string[];
  public scores: GenomicScore[];
  public defaultVisible: boolean;
}

export class AgpOrder {
  public section: string;
  public id: string;
}

export class AgpGene {
  public geneSymbol: string;
  public geneSets: string[];

  @Type(() => AgpGenomicScores)
  public genomicScores: AgpGenomicScores[];

  @Type(() => AgpStudy)
  public studies: AgpStudy[];
}

export class AgpGenomicScores {
  public id: string;

  @Type(() => AgpGenomicScoreWithValue)
  public scores: AgpGenomicScoreWithValue[];
}

export class AgpGenomicScoreWithValue {
  public id: string;
  public value: number;
  public format: string;
}

export class AgpStudy {
  public id: string;

  @Type(() => AgpPersonSet)
  public personSets: AgpPersonSet[];
}

export class AgpPersonSet {
  public id: string;

  @Type(() => AgpEffectType)
  public effectTypes: AgpEffectType[];
}

export class AgpEffectType {
  public id: string;
  public value: AgpEffectTypeValue;
}

export class AgpEffectTypeValue {
  public count: number;
  public rate: number;
}
