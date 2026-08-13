import { GenomicScoreState } from 'app/genomic-scores-block/genomic-scores-block.state';
import { Type } from 'class-transformer';

/*
 * Wire formats for `GET /api/v3/gene_profiles/single-view/configuration`.
 * The endpoint camelizes its snake_case config keys (see
 * `prepare_gp_configuration` in web_api), so the keys are camelCase here.
 *
 * Every interface carries an `[k: string]: unknown` index signature: the SPA
 * reads the fields it needs and ignores the rest, so the backend can add
 * fields without breaking parsing.
 */

interface GeneProfilesShownJson {
  category: string;
  section: string;
  id: string;
  [k: string]: unknown;
}

interface GeneProfilesGeneLinkJson {
  name: string;
  url: string;
  [k: string]: unknown;
}

interface GeneProfilesGeneSetJson {
  setId: string;
  collectionId: string;
  meta: string;
  defaultVisible: boolean;
  [k: string]: unknown;
}

interface GeneProfilesGeneSetsCategoryJson {
  category: string;
  displayName: string;
  defaultVisible: boolean;
  sets: GeneProfilesGeneSetJson[];
  [k: string]: unknown;
}

interface GeneProfilesGeneScoreJson {
  scoreName: string;
  format: string;
  meta: string;
  defaultVisible: boolean;
  [k: string]: unknown;
}

interface GeneProfilesGeneScoresCategoryJson {
  category: string;
  displayName: string;
  defaultVisible: boolean;
  scores: GeneProfilesGeneScoreJson[];
  [k: string]: unknown;
}

interface GeneProfilesGenomicScoreJson {
  name: string;
  min: number;
  max: number;
  [k: string]: unknown;
}

interface GeneProfilesDatasetStatisticJson {
  id: string;
  displayName: string;
  effects: string[];
  category: string;
  description: string;
  variantTypes: string[];
  genomicScores?: GeneProfilesGenomicScoreJson[];
  defaultVisible: boolean;
  [k: string]: unknown;
}

interface GeneProfilesDatasetPersonSetJson {
  id: string;
  displayName: string;
  collectionId: string;
  description: string;
  childrenCount: number;
  shown?: GeneProfilesDatasetStatisticJson[];
  statistics: GeneProfilesDatasetStatisticJson[];
  [k: string]: unknown;
}

interface GeneProfilesDatasetJson {
  id: string;
  displayName: string;
  meta: string;
  defaultVisible: boolean;
  shown?: GeneProfilesDatasetPersonSetJson[];
  statistics: GeneProfilesDatasetStatisticJson[];
  personSets: GeneProfilesDatasetPersonSetJson[];
  [k: string]: unknown;
}

interface GeneProfilesOrderJson {
  section: string;
  id: string;
  [k: string]: unknown;
}

export interface GeneProfilesSingleViewConfigJson {
  shown?: GeneProfilesShownJson[];
  defaultDataset: string;
  description: string;
  geneLinks?: GeneProfilesGeneLinkJson[];
  geneSets?: GeneProfilesGeneSetsCategoryJson[];
  geneScores?: GeneProfilesGeneScoresCategoryJson[];
  datasets?: GeneProfilesDatasetJson[];
  order?: GeneProfilesOrderJson[];
  pageSize: number;
  [k: string]: unknown;
}

export class GeneProfilesSingleViewConfig {
  public constructor(
    public shown: Array<{category: string; section: string; id: string}>,
    public defaultDataset: string,
    public description: string,
    public geneLinkTemplates: {name: string; url: string}[],
    public geneSets: GeneProfilesGeneSetsCategory[],
    public geneScores: GeneProfilesGeneScoresCategory[],
    public datasets: GeneProfilesDataset[],
    public order: GeneProfilesOrder[],
    public pageSize: number,
  ) {}

  public static fromJson(json: GeneProfilesSingleViewConfigJson): GeneProfilesSingleViewConfig {
    return new GeneProfilesSingleViewConfig(
      json['shown']?.map(s => ({category: s['category'], section: s['section'], id: s['id']})),
      json['defaultDataset'],
      json['description'],
      json['geneLinks']?.map(g => ({name: g['name'], url: g['url']})),
      json['geneSets']?.map(g => GeneProfilesGeneSetsCategory.fromJson(g)),
      json['geneScores']?.map(g => GeneProfilesGeneScoresCategory.fromJson(g)),
      json['datasets']?.map(d => GeneProfilesDataset.fromJson(d)),
      json['order']?.map(o => GeneProfilesOrder.fromJson(o)),
      json['pageSize'],
    );
  }
}

export class GeneProfilesGeneSetsCategory {
  public constructor(
    public category: string,
    public displayName: string,
    public defaultVisible: boolean,
    public sets: GeneProfilesGeneSet[],
  ) {}

  public static fromJson(json: GeneProfilesGeneSetsCategoryJson): GeneProfilesGeneSetsCategory {
    return new GeneProfilesGeneSetsCategory(
      json['category'],
      json['displayName'],
      json['defaultVisible'],
      json['sets'].map(s => GeneProfilesGeneSet.fromJson(s)),
    );
  }
}

export class GeneProfilesGeneSet {
  public constructor(
    public setId: string,
    public collectionId: string,
    public meta: string,
    public defaultVisible: boolean,
  ) {}

  public static fromJson(json: GeneProfilesGeneSetJson): GeneProfilesGeneSet {
    return new GeneProfilesGeneSet(
      json['setId'],
      json['collectionId'],
      json['meta'],
      json['defaultVisible'],
    );
  }
}

export class GeneProfilesGeneScoresCategory {
  public constructor(
    public category: string,
    public displayName: string,
    public defaultVisible: boolean,
    public scores: GeneProfilesGeneScore[],
  ) {}

  public static fromJson(json: GeneProfilesGeneScoresCategoryJson): GeneProfilesGeneScoresCategory {
    return new GeneProfilesGeneScoresCategory(
      json['category'],
      json['displayName'],
      json['defaultVisible'],
      json['scores'].map(s => GeneProfilesGeneScore.fromJson(s)),
    );
  }
}

export class GeneProfilesGeneScore {
  public constructor(
    public scoreName: string,
    public format: string,
    public meta: string,
    public defaultVisible: boolean,
  ) {}

  public static fromJson(json: GeneProfilesGeneScoreJson): GeneProfilesGeneScore {
    return new GeneProfilesGeneScore(
      json['scoreName'],
      json['format'],
      json['meta'],
      json['defaultVisible'],
    );
  }
}

export class GeneProfilesDataset {
  public constructor(
    public id: string,
    public displayName: string,
    public meta: string,
    public defaultVisible: boolean,
    public shown: GeneProfilesDatasetPersonSet[],
    public statistics: GeneProfilesDatasetStatistic[],
    public personSets: GeneProfilesDatasetPersonSet[],
  ) {}

  public static fromJson(json: GeneProfilesDatasetJson): GeneProfilesDataset {
    return new GeneProfilesDataset(
      json['id'],
      json['displayName'],
      json['meta'],
      json['defaultVisible'],
      json['shown']?.map(s => GeneProfilesDatasetPersonSet.fromJson(s)),
      json['statistics'].map(s => GeneProfilesDatasetStatistic.fromJson(s)),
      json['personSets'].map(p => GeneProfilesDatasetPersonSet.fromJson(p)),
    );
  }
}

export class GeneProfilesDatasetPersonSet {
  public defaultVisible = true;

  public constructor(
    public id: string,
    public displayName: string,
    public collectionId: string,
    public description: string,
    public childrenCount: number,
    public shown: GeneProfilesDatasetStatistic[],
    public statistics: GeneProfilesDatasetStatistic[],
  ) {}

  public static fromJson(json: GeneProfilesDatasetPersonSetJson): GeneProfilesDatasetPersonSet {
    return new GeneProfilesDatasetPersonSet(
      json['id'],
      json['displayName'],
      json['collectionId'],
      json['description'],
      json['childrenCount'],
      json['shown']?.map(s => GeneProfilesDatasetStatistic.fromJson(s)),
      json['statistics'].map(s => GeneProfilesDatasetStatistic.fromJson(s)),
    );
  }
}

export class GeneProfilesDatasetStatistic {
  public constructor(
    public id: string,
    public displayName: string,
    public effects: string[],
    public category: string,
    public description: string,
    public variantTypes: string[],
    public scores: GenomicScoreState[],
    public defaultVisible: boolean,
  ) {}

  public static fromJson(json: GeneProfilesDatasetStatisticJson): GeneProfilesDatasetStatistic {
    return new GeneProfilesDatasetStatistic(
      json['id'],
      json['displayName'],
      json['effects'],
      json['category'],
      json['description'],
      json['variantTypes'],
      json['genomicScores']?.map((s): GenomicScoreState => ({
        score: s['name'],
        histogramType: 'continuous',
        rangeStart: s['min'],
        rangeEnd: s['max'],
        values: null,
        categoricalView: null,
      })),
      json['defaultVisible'],
    );
  }
}

export class GeneProfilesOrder {
  public constructor(
    public section: string,
    public id: string,
  ) {}

  public static fromJson(json: GeneProfilesOrderJson): GeneProfilesOrder {
    return new GeneProfilesOrder(
      json['section'],
      json['id'],
    );
  }
}

export class GeneProfilesGene {
  public geneSymbol: string;
  public geneSets: string[];
  public geneLinks: {name: string; url: string}[];

  @Type(() => GeneProfilesGeneScores)
  public geneScores: GeneProfilesGeneScores[];

  @Type(() => GeneProfilesStudy)
  public studies: GeneProfilesStudy[];
}

export class GeneProfilesGeneScores {
  public id: string;

  @Type(() => GeneProfilesGeneScoreWithValue)
  public scores: GeneProfilesGeneScoreWithValue[];
}

export class GeneProfilesGeneScoreWithValue {
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
