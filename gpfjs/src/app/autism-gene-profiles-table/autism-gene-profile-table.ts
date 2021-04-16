import { sprintf } from 'sprintf-js';

export class AutismGeneToolConfig {
  constructor(
    private defaultDataset: string,
    private geneSets: AutismGeneToolGeneSetsCategory[],
    private genomicScores: AutismGeneToolGenomicScoresCategory[],
    private datasets: AutismGeneToolDataset[],
  ) { }

  static fromJson(json) {
    return new AutismGeneToolConfig(
      json['default_dataset'],
      this.geneSetsCategoriesFromJson(json['gene_sets']),
      this.genomicScoresFromJson(json['genomic_scores']),
      this.datasetsFromJson(json['datasets'])
    );
  }

  static datasetsFromJson(datasetsJson): Array<AutismGeneToolDataset> {
    const datasetKeys = Object.keys(datasetsJson);
    return datasetKeys.map(dataset => new AutismGeneToolDataset(dataset, datasetsJson[dataset]['effects'], datasetsJson[dataset]['person_sets']));
  }

  static geneSetsCategoriesFromJson(geneSetsCategoriesJson): Array<AutismGeneToolGeneSetsCategory> {
    const geneSetsCategoriesArray: AutismGeneToolGeneSetsCategory[] = [];

    geneSetsCategoriesJson.forEach(category => {
      geneSetsCategoriesArray.push(
        new AutismGeneToolGeneSetsCategory(
          category['category'],
          category['display_name'],
          AutismGeneToolGeneSetsCategory.setsFromJson(category['sets'])
        )
      );
    });

    return geneSetsCategoriesArray;
  }

  static genomicScoresFromJson(genomicScoresJson): Array<AutismGeneToolGenomicScoresCategory> {
    const genomicScoresArray: AutismGeneToolGenomicScoresCategory[] = [];

    genomicScoresJson.forEach(category => {
      genomicScoresArray.push(
        new AutismGeneToolGenomicScoresCategory(
          category['category'],
          category['display_name'],
          AutismGeneToolGenomicScoresCategory.scoresFromJson(category['scores'])
        )
      );
    });

    return genomicScoresArray;
  }
}

export class AutismGeneToolGeneSetsCategory {
  constructor(
    private category: string,
    private displayName: string,
    private sets: AutismGeneToolGeneSet[],
  ) { }

  static setsFromJson(setsJson): Array<AutismGeneToolGeneSet> {
    const setsArray: AutismGeneToolGeneSet[] = [];

    setsJson.forEach(set => {
      setsArray.push(new AutismGeneToolGeneSet(set['set_id'], set['collection_id']));
    });

    return setsArray;
  }
}

export class AutismGeneToolGeneSet {
  constructor(
    private setId: string,
    private collectionId: string,
  ) { }
}

export class AutismGeneToolGenomicScoresCategory {
  constructor(
    private category: string,
    private displayName: string,
    private scores: AutismGeneToolScore[],
  ) { }

  static scoresFromJson(scoresJson): Array<AutismGeneToolScore> {
    const scoresArray: AutismGeneToolScore[] = [];

    scoresJson.forEach(score => {
      scoresArray.push(new AutismGeneToolScore(score['score_name'], score['format']));
    });

    return scoresArray;
  }
}

export class AutismGeneToolScore {
  constructor(
    private scoreName: string,
    private format: string,
  ) { }
}

export class AutismGeneToolDataset {
  constructor(
    private name: string,
    private effects: string[],
    private personSets: string[],
  ) { }
}

export class AutismGeneToolGene {
  constructor (
    private geneSymbol: string,
    private geneSets: string[],
    private genomicScores: {category: string, scores: Map<string, any>}[],
    private studies: AutismGeneToolGeneStudy[]
  ) { }

  static fromJson(json) {
    const newGenomicScores = [];
    Object.entries(json['genomic_scores']).forEach(([key, value]) => {
      newGenomicScores.push({
        category: key,
        scores: new Map((Object.entries(value)).map(score => {
          score[1] = Number(sprintf(score[1]['format'], score[1]['value'])).toString();
          return score;
        }))
      });
    });

    return new AutismGeneToolGene(
      json['gene_symbol'],
      json['gene_sets'],
      newGenomicScores,
      this.geneStudiesFromJson(json['studies'])
    );
  }

  static geneStudiesFromJson(geneStudiesJson): Array<AutismGeneToolGeneStudy> {
    const geneStudyKeys = Object.keys(geneStudiesJson);
    return geneStudyKeys.map(geneStudy => new AutismGeneToolGeneStudy(geneStudy, this.personSetsFromJson(geneStudiesJson[geneStudy])));
  }

  static personSetsFromJson(personSetsJson): Array<AutismGeneToolPersonSet> {
    const personSetsKeys = Object.keys(personSetsJson);
    return personSetsKeys.map(personSet => new AutismGeneToolPersonSet(personSet, new Map(Object.entries(personSetsJson[personSet]))));
  }
}

export class AutismGeneToolGeneStudy {
  constructor (
    private name: string,
    private personSets: AutismGeneToolPersonSet[],

  ) { }
}

export class AutismGeneToolPersonSet {
  constructor (
    private name: string,
    private effectTypes: Map<String, String>,
  ) { }
}
