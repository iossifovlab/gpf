import { PedigreeData } from '../genotype-preview-model/genotype-preview';

export class ChildrenCounter {

  static fromJson(json: any, row: string) {
    return new ChildrenCounter(
      row,
      json['column'],
      json[row]
    );
  }

  constructor(
    readonly row: string,
    readonly column: string,
    readonly children: number,
  ) {}
}

export class GroupCounter {

  static fromJson(json: any, rows: string[]) {
    return new GroupCounter(
      json['column'],
      rows.map(row => ChildrenCounter.fromJson(json, row))
    );
  }

  constructor(
    readonly column: string,
    readonly childrenCounters: ChildrenCounter[]
  ) {}
}

export class PeopleCounter {

  static fromJson(json: any) {
    return new PeopleCounter(
      json['counters'].map(
        childCounter => GroupCounter.fromJson(childCounter, json['rows'])),
      json['group_name'],
      json['rows'],
      json['columns']
    );
  }

  constructor(
    readonly groupCounters: GroupCounter[],
    readonly groupName: string,
    readonly rows: string[],
    readonly columns: string[]
    ) {}

  getChildrenCounter(column: string, row: string) {
    let columnGroupCounter = this.groupCounters.filter(
      groupCounter => groupCounter.column === column)[0];
    let rowChildrenCounter = columnGroupCounter.childrenCounters.filter(
      childrenCounter => childrenCounter.row === row)[0];

    return rowChildrenCounter;
  }
}

export class PeopleReport {
  static fromJson(json: any) {
    return new PeopleReport(
      json['people_counters'].map(peopleCounter => PeopleCounter.fromJson(peopleCounter)));
  }

  constructor(
    readonly peopleCounters: PeopleCounter[],
  ) {}
}

export class PedigreeCounter {

  static fromArray(data: any) {
    return new PedigreeCounter(
      data['pedigree'].map(pedigreeData => PedigreeData.fromArray(pedigreeData)),
      data['pedigrees_count']);
  }

  constructor(
    readonly data: PedigreeData[],
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
      json['families_counters'].map(
        familyCounters => FamilyCounters.fromJson(familyCounters)),
      json['families_total'],
    );
  }

  constructor(
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
      json['columns'],
      json['effect_groups'],
      json['effect_types']
      );
    }

    constructor(
      readonly rows: EffectTypeRow[],
      readonly groupName: string,
      readonly columns: string[],
      readonly effectGroups: string[],
      readonly effectTypes: string[]
      ) {}
    }

    export class DenovoReport {

      static fromJson(json: any) {
        if (!json) {
          return null;
        }
        return new DenovoReport(
          json['tables'].map(table => EffectTypeTable.fromJson(table))
        );
      }

      constructor(
        readonly tables: EffectTypeTable[]
  ) {}
}

export class VariantReport {

  static fromJson(json: any) {
    return new VariantReport(
      json['id'],
      json['study_name'],
      json['study_description'],
      PeopleReport.fromJson(json['people_report']),
      FamilyReport.fromJson(json['families_report']),
      DenovoReport.fromJson(json['denovo_report'])
    );
  }

  constructor(
    readonly id: string,
    readonly studyName: string,
    readonly studyDescription: string,
    readonly peopleReport: PeopleReport,
    readonly familyReport: FamilyReport,
    readonly denovoReport: DenovoReport
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

export enum PeopleSex {
  people_male = 'Male',
  people_female = 'Female',
  people_unspecified = 'Unspecified',
  people_total = 'Total'
}
