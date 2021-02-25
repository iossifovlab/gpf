export class AutismGeneToolConfig {
  constructor(
    private autismScores: string[],
    private datasets: AutismGeneToolDataset[],
    private geneSets: string[],
    private protectionScores: string[],
  ) { }

  static fromJson(json: any) {
    return new AutismGeneToolConfig(
      json['autism_scores'],
      this.datasetsFromJson(json['datasets']),
      json['gene_sets'],
      json['protection_scores']
    );
  }

  static datasetsFromJson(datasetsJson: any): Array<AutismGeneToolDataset> {
    const datasetKeys = Object.keys(datasetsJson);
    return datasetKeys.map(dataset => new AutismGeneToolDataset(dataset, datasetsJson[dataset]['effects'], datasetsJson[dataset]['person_sets']));
  }
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
    private autismScores: Map<string, number>,
    private protectionScores: Map<string, number>,
    private studies: AutismGeneToolGeneStudy[]
  ) { }

  static fromJson(json: any) {
    return new AutismGeneToolGene(
      json['gene_symbol'],
      json['gene_sets'],
      new Map(Object.entries(json['autism_scores'])),
      new Map(Object.entries(json['protection_scores'])),
      this.geneStudiesFromJson(json['studies']),
    );
  }

  static geneStudiesFromJson(geneStudiesJson: any): Array<AutismGeneToolGeneStudy> {
    const geneStudyKeys = Object.keys(geneStudiesJson);
    return geneStudyKeys.map(geneStudy => new AutismGeneToolGeneStudy(geneStudy, this.personSetsFromJson(geneStudiesJson[geneStudy])));
  }

  static personSetsFromJson(personSetsJson: any): Array<AutismGeneToolPersonSet> {
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
