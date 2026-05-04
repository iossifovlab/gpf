import { PedigreeData } from '../genotype-preview-model/genotype-preview';

export class ChildrenCounter {
  public static fromJson(json: object, row: string): ChildrenCounter {
    return new ChildrenCounter(row, json['column'] as string, json[row] as number);
  }

  public constructor(
    public readonly row: string,
    public readonly column: string,
    public readonly children: number
  ) {}
}

export class GroupCounter {
  public static fromJson(json: object, rows: string[]): GroupCounter {
    return new GroupCounter(
      json['column'] as string,
      rows.map((row) => ChildrenCounter.fromJson(json, row))
    );
  }

  public constructor(
    public readonly column: string,
    public readonly childrenCounters: ChildrenCounter[]
  ) {}
}

export class PeopleCounter {
  public static fromJson(json: object): PeopleCounter {
    return new PeopleCounter(
      json['counters'].map(
        (childCounter: ChildrenCounter) => GroupCounter.fromJson(childCounter, json['rows'] as string[])
      ) as GroupCounter[],
      json['group_name'] as string,
      json['rows'] as string[],
      json['columns'] as string[]
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
      json.map((peopleCounter: PeopleCounter) => PeopleCounter.fromJson(peopleCounter)) as PeopleCounter[]
    );
  }

  public constructor(
    public readonly peopleCounters: PeopleCounter[]
  ) {}
}

export class PedigreeCounter {
  public static fromJson(json: object, groupName: string): PedigreeCounter {
    return new PedigreeCounter(
      json['counter_id'] as number,
      groupName,
      json['pedigree'].map(
        (pedigreeCounter: PedigreeCounter[]) => PedigreeData.fromArray(pedigreeCounter)
      ) as PedigreeData[],
      json['pedigrees_count'] as number,
      json['tags'] as string[]
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
  public static fromJson(json: object): FamilyCounter {
    return new FamilyCounter(
      json['counters'].map(
        (familyCounter: FamilyCounter) => PedigreeCounter.fromJson(familyCounter, json['group_name'] as string)
      ) as PedigreeCounter[],
      json['group_name'] as string,
      json['phenotypes'] as string[],
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
      json.map((familyCounters: FamilyCounter) => FamilyCounter.fromJson(familyCounters)) as FamilyCounter[],
      families
    );
  }

  public constructor(
    public readonly familiesCounters: FamilyCounter[],
    public readonly familiesTotal: number
  ) {}
}

export class DeNovoData {
  public static fromJson(json: object): DeNovoData {
    return new DeNovoData(
      json['column'] as string,
      json['number_of_observed_events'] as number,
      json['number_of_children_with_event'] as number,
      json['observed_rate_per_child'] as number,
      json['percent_of_children_with_events'] as number
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
  public static fromJson(json: object): EffectTypeRow {
    return new EffectTypeRow(
      json['effect_type'] as string,
      json['row'].map((data: DeNovoData) => DeNovoData.fromJson(data)) as DeNovoData[]
    );
  }

  public constructor(public readonly effectType: string, public readonly data: DeNovoData[]) {}
}

export class EffectTypeTable {
  public static fromJson(json: object): EffectTypeTable {
    return new EffectTypeTable(
      json['rows'].map((row: EffectTypeRow) => EffectTypeRow.fromJson(row)) as EffectTypeRow[],
      json['group_name'] as string,
      json['columns'] as string[],
      json['effect_groups'] as string[],
      json['effect_types'] as string[]
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
      json['tables'].map((table: EffectTypeTable) => EffectTypeTable.fromJson(table)) as EffectTypeTable[]
    );
  }

  public constructor(
    public readonly tables: EffectTypeTable[]
  ) {}
}

export class VariantReport {
  public static fromJson(json: object): VariantReport {
    return new VariantReport(
      json['id'] as string,
      json['study_name'] as string,
      json['study_description'] as string,
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
  public static fromJson(json: object): LegendItem {
    return new LegendItem(json['id'] as string, json['name'] as string, json['color'] as string);
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
      list.map((legendItem) => LegendItem.fromJson(legendItem as object))
    );
  }

  public constructor(
    public readonly legendItems: LegendItem[]
  ) {}
}
