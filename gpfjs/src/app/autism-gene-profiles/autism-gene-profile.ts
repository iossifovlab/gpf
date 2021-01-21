export class AutismGeneToolConfig {
  constructor(
    private autism_scores: string[],
    private datasets: AutismGeneToolDataset[],
    private geneLists: string[],
    private geneSymbols: string[],
    private protectionScore: string[],
  ) { }

  static fromJson(json: any) {
    return new AutismGeneToolConfig(
      json['autism_scores'],
      this.datasetsFromJson(json['datasets']),
      json['gene_lists'],
      json['gene_symbols'],
      json['protection_scores']
    );
  }

  static datasetsFromJson(datasetsJson: any): Array<AutismGeneToolDataset> {
    const datasetKeys = Object.keys(datasetsJson);
    return datasetKeys
      .map(dataset => {
        return AutismGeneToolDataset.fromJson(
          dataset, datasetsJson[dataset]['effects'], datasetsJson[dataset]['person_sets']
        )
      });
  }
}

export class AutismGeneToolDataset {
  constructor(
    private name: string,
    private effects: string[],
    private personSets: string[],
  ) { }

  static fromJson(name: string, effects: string[], personSets: string[]) {
    return new AutismGeneToolDataset(name, effects, personSets);
  }
}

export class AutismGeneToolGene {
  constructor (
    private geneSymbol: string,
    private geneSets: string[],
    private autismScores: Map<String, Number>,
    private protectionScores: Map<String, Number>,
    private studies: GeneStudy[]
  ) { }

  static fromJson(json: any) {
    console.log(new Map(Object.entries(json['autism_scores'])))
    return new AutismGeneToolGene(
      json['gene_symbol'],
      json['gene_sets'],
      new Map(Object.entries(json['autism_scores'])),
      new Map(Object.entries(json['protection_scores'])),
      this.geneStudiesFromJson(json['studies']),
    );
  }

  geneStudiesFromJson(geneStudiesJson: any): Array<GeneStudy> {
    const datasetKeys = Object.keys(datasetsJson);
    return datasetKeys
      .map(dataset => {
        return AutismGeneToolDataset.fromJson(
          dataset, datasetsJson[dataset]['effects'], datasetsJson[dataset]['person_sets']
        )
      });
  }


}

export class GeneStudy {
  constructor (
    private name: string,
    private personSets: PersonSet[],

  ) { }

  fromJson(json: any) {
    return new PersonSet(name, );
  }

}

export class PersonSet {
  constructor (
    private name: string,
    private effectTypes: Map<String, Number>,
  ) { }

  fromJson(json: any) {
    return new PersonSet(name, );
  }
}
