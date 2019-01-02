import { PedigreeData } from '../genotype-preview-model/genotype-preview';

export class Study {

  static fromJsonArray(json: any[]) {
    return new Study(json['study_name'], json['study_description']);
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
      json['column'],
      json['people_male'],
      json['people_female'],
      json['people_unspecified'],
      json['people_total'],
    );
  }

  constructor(
    readonly column: string,
    readonly childrenMale: number,
    readonly childrenFemale: number,
    readonly childrenUnspecified: number,
    readonly childrenTotal: number,
  ) {}
}

export class PeopleCounter {

  static fromJson(json: any) {
    return new PeopleCounter(
      json['counters'].map(
        childCounter => ChildrenCounter.fromJson(childCounter)),
      json['group_name'],
      json['columns']
    );
  }

  constructor(
    readonly childrenCounters: ChildrenCounter[],
    readonly groupName: string,
    readonly columns: string[]
    ) {}
}

export class PedigreeCounter {

  static fromArray(data: any) {
    return new PedigreeCounter(
      data['pedigree'].map(pedigreeData => PedigreeData.fromArray(pedigreeData)),
      data['pedigrees_count']);
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
        pedigree => PedigreeCounter.fromArray(pedigree)
      )
    );
  }

  constructor(
    readonly pedigreeCounters: PedigreeCounter[],
  ) {}
}

export class FamilyCounters {

  static fromJson(json: any) {
    return new FamilyCounters(
      json['counters'].map(
        family_counter => FamilyCounter.fromJson(family_counter)
      ),
      json['group_name'],
      json['phenotypes'],
      Legend.fromList(json['legend'])
    );
  }

  constructor(
    readonly familyCounter: FamilyCounter[],
    readonly groupName: string,
    readonly phenotypes: string[],
    readonly legend: Legend
  ) {}
}

export class FamilyReport {

  static fromJson(json: any) {
    return new FamilyReport(
      json['people_counters'].map(
        peopleCounter => PeopleCounter.fromJson(peopleCounter)),
      json['families_counters'].map(
        familyCounters => FamilyCounters.fromJson(familyCounters)),
      json['families_total'],
    );
  }

  constructor(
    readonly peopleCounters: PeopleCounter[],
    readonly familiesCounters: FamilyCounters[],
    readonly familiesTotal: number,
  ) {}

}

export class DeNovoData {

  static fromJson(json: any) {
    return new DeNovoData(
      json['column'],
      json['number_of_observed_events'],
      json['number_of_children_with_event'],
      json['observed_rate_per_child'],
      json['percent_of_children_with_events'],
    );
  }

  constructor(
    readonly column: string,
    readonly numberOfObservedEvents: number,
    readonly numberOfChildrenWithEvent: number,
    readonly observedRatePerChild: number,
    readonly percentOfChildrenWithEvents: number,
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

export class EffectTypeTable {

  static fromJson(json: any) {
    return new EffectTypeTable(
      json['rows'].map(row => EffectTypeRow.fromJson(row)),
      json['group_name'],
      json['columns']
      );
    }

    constructor(
      readonly rows: EffectTypeRow[],
      readonly groupName: string,
      readonly columns: string[]
      ) {}
    }

    export class DenovoReport {

      static fromJson(json: any) {
        if (!json) {
          return null;
        }
        return new DenovoReport(
          json['tables'].map(table => EffectTypeTable.fromJson(table)),
          json['effect_groups'],
          json['effect_types']
        );
      }

      constructor (
        readonly tables: EffectTypeRow[],
        readonly effectGroups: string[],
        readonly effectTypes: string[],
  ) {}
}

export class VariantReport {

  static fromJson(json: any) {
    return new VariantReport(
      json['study_name'],
      json['study_description'],
      FamilyReport.fromJson(json['families_report']),
      DenovoReport.fromJson(json['denovo_report']),
      json['is_downloadable']
    );
  }

  constructor(
    readonly studyName: string,
    readonly studyDescription: string,
    readonly familyReport: FamilyReport,
    readonly denovoReport: DenovoReport,
    readonly isDownloadable: boolean


  ) {}

}

export class PedigreeTable {

  constructor(
    readonly pedigrees: PedigreeCounter[][],
    readonly phenotypes: string[],
    readonly groupName: string,
    readonly legend: Legend
  ) {}

}

export class LegendItem {

  static fromJson(json: any) {
    return new LegendItem(
      json['id'],
      json['name'],
      json['color']
    );
  }

  constructor(
    readonly id: string,
    readonly name: string,
    readonly color: string
  ) {}
}

export class Legend {

  static fromList(list: any[]) {
    return new Legend(
      list.map(legendItem => LegendItem.fromJson(legendItem))
    );
  }

  constructor(
    readonly legendItems: LegendItem[]
  ) {}
}
