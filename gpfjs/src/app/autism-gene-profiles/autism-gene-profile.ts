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
