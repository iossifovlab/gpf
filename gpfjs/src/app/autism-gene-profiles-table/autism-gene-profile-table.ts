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

  public get shownGeneSets(): AgpGeneSetsCategory[] {
    return this.geneSets.filter(gs => gs.defaultVisible);
  }

  public get shownGenomicScores(): AgpGenomicScoresCategory[] {
    return this.genomicScores.filter(gs => gs.defaultVisible);
  }

  public get shownDatasets(): AgpDataset[] {
    return this.datasets.filter(d => d.defaultVisible);
  }
  
}

export class AgpGeneSetsCategory {
  category: string;
  displayName: string;
  defaultVisible: boolean;

  @Type(() => AgpGeneSet)
  sets: AgpGeneSet[];

  public get itemIds(): string[] {
    return this.sets.map(set => set.setId);
  }

  public get shown(): AgpGeneSet[] {
    return this.sets.filter(set => set.defaultVisible);
  }

  public get shownItemIds(): string[] {
    return this.sets.filter(set => set.defaultVisible).map(set => set.setId);
  }
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

  public get itemIds(): string[] {
    return this.scores.map(score => score.scoreName);
  }

  public get shown(): AgpGenomicScore[] {
    return this.scores.filter(score => score.defaultVisible);
  }

  public get shownItemIds(): string[] {
    return this.scores.filter(score => score.defaultVisible).map(score => score.scoreName);
  }
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

  public get itemIds(): string[] {
    return this.personSets.map(ps => ps.id);
  }

  public get shown(): AgpDatasetPersonSet[] {
    return this.personSets.filter(ps => ps.defaultVisible);
  }

  public get shownItemIds(): string[] {
    return this.personSets.filter(ps => ps.defaultVisible).map(ps => ps.id);
  }
}

export class AgpDatasetPersonSet {
  id: string;
  displayName: string;
  collectionId: string;
  description: string;
  parentsCount: number;
  childrenCount: number;
  defaultVisible = true;
  
  @Type(() => AgpDatasetStatistic)
  statistics: AgpDatasetStatistic[];

  public get itemIds(): string[] {
    return this.statistics.map(s => s.id);
  }

  public get shown(): AgpDatasetStatistic[] {
    return this.statistics.filter(s => s.defaultVisible);
  }

  public get shownItemIds(): string[] {
    return this.statistics.filter(s => s.defaultVisible).map(s => s.id);
  }
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
