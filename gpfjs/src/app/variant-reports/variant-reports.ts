import { PedigreeData } from '../genotype-preview-table/genotype-preview';

export class Study {

  static fromJsonArray(json: any[]) {
    return new Study(json[0], json[1]);
  }

  constructor(
    readonly name: string,
    readonly description: string
  ) {}
}

export class Studies {

    static fromJson(json: any) {
      return new Studies(json['report_studies']
        .map(study => Study.fromJsonArray(study)));
    }

    constructor(
      readonly studies: Study[]
    ) {}

}

export class ChildrenCounter {

  static fromJson(json: any) {
    return new ChildrenCounter(
      json['phenotype'],
      json['children_male'],
      json['children_female'],
      json['children_total'],
    );
  }

  constructor(
    readonly phenotype: string,
    readonly childrenMale: number,
    readonly childrenFemale: number,
    readonly childrenTotal: number,
  ) {}
}

export class PedigreeCounter {

  static fromArray(data: any) {
    return new PedigreeCounter(
      data[0].map(pedigreeData => PedigreeData.fromArray(pedigreeData)),
      data[1]);
  }

  constructor(
    readonly data: PedigreeData,
    readonly count: number
  ) {}
}

export class FamilyCounter {

  static fromJson(json: any) {
    return new FamilyCounter(
      json['counters'].map(
        pedigree => PedigreeCounter.fromArray(pedigree)),
      json['phenotype']
    );
  }

  constructor(
    readonly pedigreeCounters: PedigreeCounter[],
    readonly phenotype: string
  ) {}
}

export class FamilyReport {

  static fromJson(json: any) {
    return new FamilyReport(
      json['phenotypes'],
      json['children_counters'].map(
        childCounter => ChildrenCounter.fromJson(childCounter)),
      json['families_counters'].map(
        familyCounter => FamilyCounter.fromJson(familyCounter)),
      json['families_total'],
    );
  }

  constructor(
    readonly phenotypes: string[],
    readonly childrenCounters: ChildrenCounter[],
    readonly familiesCounters: FamilyCounter[],
    readonly familiesTotal: number,
  ) {}

}

export class DeNovoData {

  static fromJson(json: any) {
    return new DeNovoData(
      json['phenotype'],
      json['events_count'],
      json['events_children_count'],
      json['events_rate_per_child'],
      json['events_children_percent'],
    );
  }

  constructor(
    readonly phenotype: string,
    readonly eventsCount: number,
    readonly eventsChildrenCount: number,
    readonly eventsRatePerChild: number,
    readonly eventsChildrenPercent: number,
  ) {}
}

export class EffectTypeRow {

  static fromJson(json: any) {
    return new EffectTypeRow(
      json['effect_type'],
      json['row'].map(data => DeNovoData.fromJson(data))
    );
  }

  constructor(
    readonly effectType: string,
    readonly data: DeNovoData[]

  ) {}
}

export class DenovoReport {

  static fromJson(json: any) {
    return new DenovoReport(
      json['phenotypes'],
      json['effect_groups'],
      json['effect_types'],
      json['rows'].map(row => EffectTypeRow.fromJson(row))
    );
  }


  constructor (
    readonly phenotypes: string[],
    readonly effectGroups: string[],
    readonly effectTypes: string[],
    readonly row: EffectTypeRow[]
  ) {}
}

export class VariantReport {

  static fromJson(json: any) {
    return new VariantReport(
      json['study_name'],
      json['study_description'],
      FamilyReport.fromJson(json['families_report']),
      DenovoReport.fromJson(json['denovo_report'])
    );
  }

  constructor(
    readonly studyName: string,
    readonly studyDescription: string,
    readonly familyReport: FamilyReport,
    readonly denovoReport: DenovoReport


  ) {}

}
