import { PedigreeData } from '../genotype-preview-model/genotype-preview';

export class ChildrenCounter {
  public static fromJson(json: any, row: string): ChildrenCounter {
    return new ChildrenCounter(row, json['column'], json[row]);
  }

  public constructor(
    public readonly row: string,
    public readonly column: string,
    public readonly children: number
  ) {}
}

export class GroupCounter {
  public static fromJson(json: any, rows: string[]): GroupCounter {
    return new GroupCounter(
      json['column'],
      rows.map((row) => ChildrenCounter.fromJson(json, row))
    );
  }

  public constructor(
    public readonly column: string,
    public readonly childrenCounters: ChildrenCounter[]
  ) {}
}

export class PeopleCounter {
  public static fromJson(json: any): PeopleCounter {
    return new PeopleCounter(
      json['counters'].map((childCounter: any) => GroupCounter.fromJson(childCounter, json['rows'])),
      json['group_name'],
      json['rows'],
      json['columns']
    );
  }

  public constructor(
    public readonly groupCounters: GroupCounter[],
    public readonly groupName: string,
    public readonly rows: string[],
    public readonly columns: string[]
  ) {}

  public getChildrenCounter(column: string, row: string): ChildrenCounter {
    const columnGroupCounter = this.groupCounters.filter(
      (groupCounter) => groupCounter.column === column
    )[0];
    const rowChildrenCounter = columnGroupCounter.childrenCounters.filter(
      (childrenCounter) => childrenCounter.row === row
    )[0];

    return rowChildrenCounter;
  }
}

export class PeopleReport {
  public static fromJson(json: any): PeopleReport {
    return new PeopleReport(
      json.map((peopleCounter: any) => PeopleCounter.fromJson(peopleCounter))
    );
  }

  public constructor(
    public readonly peopleCounters: PeopleCounter[]
  ) {}
}

export class PedigreeCounter {
  public static fromJson(json: any, groupName: string): PedigreeCounter {
    return new PedigreeCounter(
      json['counter_id'],
      groupName,
      json['pedigree'].map((pedigreeCounter) => PedigreeData.fromArray(pedigreeCounter)),
      json['pedigrees_count'],
      json['tags']
    );
  }

  public constructor(
    public readonly counterId: number,
    public readonly groupName: string,
    public readonly data: PedigreeData[],
    public readonly count: number,
    public readonly tags: string[]
  ) {}
}

export class FamilyCounter {
  public static fromJson(json: any): FamilyCounter {
    return new FamilyCounter(
      json['counters'].map((family_counter: any) => PedigreeCounter.fromJson(family_counter, json['group_name'])),
      json['group_name'],
      json['phenotypes'],
      Legend.fromList(json['legend'])
    );
  }

  public constructor(
    public readonly pedigreeCounters: PedigreeCounter[],
    public readonly groupName: string,
    public readonly phenotypes: string[],
    public readonly legend: Legend
  ) {}
}

export class FamilyReport {
  public static fromJson(json: any, families = 0): FamilyReport {
    return new FamilyReport(
      json.map((familyCounters: any) => FamilyCounter.fromJson(familyCounters)),
      families
    );
  }

  public constructor(
    public readonly familiesCounters: FamilyCounter[],
    public readonly familiesTotal: number
  ) {}
}

export class DeNovoData {
  public static fromJson(json: any): DeNovoData {
    return new DeNovoData(
      json['column'],
      json['number_of_observed_events'],
      json['number_of_children_with_event'],
      json['observed_rate_per_child'],
      json['percent_of_children_with_events']
    );
  }

  public constructor(
    public readonly column: string,
    public readonly numberOfObservedEvents: number,
    public readonly numberOfChildrenWithEvent: number,
    public readonly observedRatePerChild: number,
    public readonly percentOfChildrenWithEvents: number
  ) {}
}

export class EffectTypeRow {
  public static fromJson(json: any): EffectTypeRow {
    return new EffectTypeRow(
      json['effect_type'],
      json['row'].map((data: any) => DeNovoData.fromJson(data))
    );
  }

  constructor(public readonly effectType: string, public readonly data: DeNovoData[]) {}
}

export class EffectTypeTable {
  public static fromJson(json: any): EffectTypeTable {
    return new EffectTypeTable(
      json['rows'].map((row: any) => EffectTypeRow.fromJson(row)),
      json['group_name'],
      json['columns'],
      json['effect_groups'],
      json['effect_types']
    );
  }

  public constructor(
    public readonly rows: EffectTypeRow[],
    public readonly groupName: string,
    public readonly columns: string[],
    public readonly effectGroups: string[],
    public readonly effectTypes: string[]
  ) {}
}

export class DenovoReport {
  public static fromJson(json: any): DenovoReport {
    if (!json) {
      return null;
    }
    return new DenovoReport(
      json['tables'].map((table: any) => EffectTypeTable.fromJson(table))
    );
  }

  public constructor(
    public readonly tables: EffectTypeTable[]
  ) {}
}

export class VariantReport {
  public static fromJson(json: any) {
    return new VariantReport(
      json['id'],
      json['study_name'],
      json['study_description'],
      PeopleReport.fromJson(json['people_report']),
      FamilyReport.fromJson(json['families_report'], json['families'] as number),
      DenovoReport.fromJson(json['denovo_report'])
    );
  }

  public constructor(
    public readonly id: string,
    public readonly studyName: string,
    public readonly studyDescription: string,
    public readonly peopleReport: PeopleReport,
    public readonly familyReport: FamilyReport,
    public readonly denovoReport: DenovoReport
  ) {}
}

export class PedigreeTable {
  public constructor(
    public pedigrees: PedigreeCounter[][],
    public readonly phenotypes: string[],
    public readonly groupName: string,
    public readonly legend: Legend
  ) {}
}

export class LegendItem {
  public static fromJson(json: any): LegendItem {
    return new LegendItem(json['id'], json['name'], json['color']);
  }

  public constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly color: string
  ) {}
}

export class Legend {
  public static fromList(list: any[]): Legend {
    return new Legend(
      list.map((legendItem) => LegendItem.fromJson(legendItem))
    );
  }

  public constructor(
    public readonly legendItems: LegendItem[]
  ) {}
}
