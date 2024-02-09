import { GenomicScore } from 'app/genotype-browser/genotype-browser';
import { Type } from 'class-transformer';

export class GeneProfilesSingleViewConfig {
  public shown: Array<{category: any; section: string; id: string}>;
  public defaultDataset: string;

  @Type(() => GeneProfilesGeneSetsCategory)
  public geneSets: GeneProfilesGeneSetsCategory[];

  @Type(() => GeneProfilesGenomicScoresCategory)
  public genomicScores: GeneProfilesGenomicScoresCategory[];

  @Type(() => GeneProfilesDataset)
  public datasets: GeneProfilesDataset[];

  @Type(() => GeneProfilesOrder)
  public order: GeneProfilesOrder[];

  public pageSize: number;
}

export class GeneProfilesGeneSetsCategory {
  public category: string;
  public displayName: string;
  public defaultVisible: boolean;

  @Type(() => GeneProfilesGeneSet)
  public sets: GeneProfilesGeneSet[];
}

export class GeneProfilesGeneSet {
  public setId: string;
  public collectionId: string;
  public meta: string;
  public defaultVisible: boolean;
}

export class GeneProfilesGenomicScoresCategory {
  public category: string;
  public displayName: string;
  public defaultVisible: boolean;

  @Type(() => GeneProfilesGenomicScore)
  public scores: GeneProfilesGenomicScore[];
}

export class GeneProfilesGenomicScore {
  public scoreName: string;
  public format: string;
  public meta: string;
  public defaultVisible: boolean;
}

export class GeneProfilesDataset {
  public id: string;
  public displayName: string;
  public meta: string;
  public defaultVisible: boolean;

  public shown: GeneProfilesDatasetPersonSet[];
  public statistics: GeneProfilesDatasetStatistic[];

  @Type(() => GeneProfilesDatasetPersonSet)
  public personSets: GeneProfilesDatasetPersonSet[];
}

export class GeneProfilesDatasetPersonSet {
  public id: string;
  public displayName: string;
  public collectionId: string;
  public description: string;
  public parentsCount: number;
  public childrenCount: number;
  public defaultVisible = true;

  public shown: GeneProfilesDatasetStatistic[];

  @Type(() => GeneProfilesDatasetStatistic)
  public statistics: GeneProfilesDatasetStatistic[];
}

export class GeneProfilesDatasetStatistic {
  public id: string;
  public displayName: string;
  public effects: string[];
  public category: string;
  public description: string;
  public variantTypes: string[];
  public scores: GenomicScore[];
  public defaultVisible: boolean;
}

export class GeneProfilesOrder {
  public section: string;
  public id: string;
}

export class GeneProfilesGene {
  public geneSymbol: string;
  public geneSets: string[];

  @Type(() => GeneProfilesGenomicScores)
  public genomicScores: GeneProfilesGenomicScores[];

  @Type(() => GeneProfilesStudy)
  public studies: GeneProfilesStudy[];
}

export class GeneProfilesGenomicScores {
  public id: string;

  @Type(() => GeneProfilesGenomicScoreWithValue)
  public scores: GeneProfilesGenomicScoreWithValue[];
}

export class GeneProfilesGenomicScoreWithValue {
  public id: string;
  public value: number;
  public format: string;
}

export class GeneProfilesStudy {
  public id: string;

  @Type(() => GeneProfilesPersonSet)
  public personSets: GeneProfilesPersonSet[];
}

export class GeneProfilesPersonSet {
  public id: string;

  @Type(() => GeneProfilesEffectType)
  public effectTypes: GeneProfilesEffectType[];
}

export class GeneProfilesEffectType {
  public id: string;
  public value: GeneProfilesEffectTypeValue;
}

export class GeneProfilesEffectTypeValue {
  public count: number;
  public rate: number;
}
