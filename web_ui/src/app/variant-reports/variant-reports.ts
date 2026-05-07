import { PedigreeData } from '../genotype-preview-model/genotype-preview';

// JSON wire formats served by the GPF /api/v3/common_reports endpoint.
// Field names match the backend's snake_case keys verbatim. The
// `[k: string]: unknown` index signature on each interface lets the
// backend add fields without breaking parsing — the SPA reads what it
// needs and ignores the rest.

interface LegendItemJson {
  id: string;
  name: string;
  color: string;
  [k: string]: unknown;
}

// Each column is a row-name → count map plus the column label.
type GroupCounterJson = { column: string } & Record<string, number | string>;

interface PeopleCounterJson {
  counters: GroupCounterJson[];
  group_name: string;
  rows: string[];
  columns: string[];
  [k: string]: unknown;
}

interface PedigreeCounterJson {
  counter_id: number;
  pedigree: unknown[][];
  pedigrees_count: number;
  tags: string[];
  [k: string]: unknown;
}

interface FamilyCounterJson {
  counters: PedigreeCounterJson[];
  group_name: string;
  phenotypes: string[];
  legend: LegendItemJson[];
  [k: string]: unknown;
}

interface DeNovoDataJson {
  column: string;
  number_of_observed_events: number;
  number_of_children_with_event: number;
  observed_rate_per_child: number;
  percent_of_children_with_events: number;
  [k: string]: unknown;
}

interface EffectTypeRowJson {
  effect_type: string;
  row: DeNovoDataJson[];
  [k: string]: unknown;
}

interface EffectTypeTableJson {
  rows: EffectTypeRowJson[];
  group_name: string;
  columns: string[];
  effect_groups: string[];
  effect_types: string[];
  [k: string]: unknown;
}

interface DenovoReportJson {
  tables: EffectTypeTableJson[];
  [k: string]: unknown;
}

export interface VariantReportJson {
  id: string;
  study_name: string;
  study_description: string;
  people_report: PeopleCounterJson[];
  families_report: FamilyCounterJson[];
  families: number;
  denovo_report: DenovoReportJson | null;
  [k: string]: unknown;
}

export class ChildrenCounter {
  public static fromJson(json: GroupCounterJson, row: string): ChildrenCounter {
    return new ChildrenCounter(row, json.column, json[row] as number);
  }

  public constructor(
    public readonly row: string,
    public readonly column: string,
    public readonly children: number
  ) {}
}

export class GroupCounter {
  public static fromJson(json: GroupCounterJson, rows: string[]): GroupCounter {
    return new GroupCounter(
      json.column,
      rows.map((row) => ChildrenCounter.fromJson(json, row))
    );
  }

  public constructor(
    public readonly column: string,
    public readonly childrenCounters: ChildrenCounter[]
  ) {}
}

export class PeopleCounter {
  public static fromJson(json: PeopleCounterJson): PeopleCounter {
    return new PeopleCounter(
      json.counters.map((counter) => GroupCounter.fromJson(counter, json.rows)),
      json.group_name,
      json.rows,
      json.columns
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
  public static fromJson(json: PeopleCounterJson[]): PeopleReport {
    return new PeopleReport(
      json.map((peopleCounter) => PeopleCounter.fromJson(peopleCounter))
    );
  }

  public constructor(
    public readonly peopleCounters: PeopleCounter[]
  ) {}
}

export class PedigreeCounter {
  public static fromJson(json: PedigreeCounterJson, groupName: string): PedigreeCounter {
    return new PedigreeCounter(
      json.counter_id,
      groupName,
      json.pedigree.map((pedigreeRow) => PedigreeData.fromArray(pedigreeRow)),
      json.pedigrees_count,
      json.tags
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
  public static fromJson(json: FamilyCounterJson): FamilyCounter {
    return new FamilyCounter(
      json.counters.map((counter) => PedigreeCounter.fromJson(counter, json.group_name)),
      json.group_name,
      json.phenotypes,
      Legend.fromList(json.legend)
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
  public static fromJson(json: FamilyCounterJson[], families = 0): FamilyReport {
    return new FamilyReport(
      json.map((familyCounter) => FamilyCounter.fromJson(familyCounter)),
      families
    );
  }

  public constructor(
    public readonly familiesCounters: FamilyCounter[],
    public readonly familiesTotal: number
  ) {}
}

export class DeNovoData {
  public static fromJson(json: DeNovoDataJson): DeNovoData {
    return new DeNovoData(
      json.column,
      json.number_of_observed_events,
      json.number_of_children_with_event,
      json.observed_rate_per_child,
      json.percent_of_children_with_events
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
  public static fromJson(json: EffectTypeRowJson): EffectTypeRow {
    return new EffectTypeRow(
      json.effect_type,
      json.row.map((data) => DeNovoData.fromJson(data))
    );
  }

  public constructor(public readonly effectType: string, public readonly data: DeNovoData[]) {}
}

export class EffectTypeTable {
  public static fromJson(json: EffectTypeTableJson): EffectTypeTable {
    return new EffectTypeTable(
      json.rows.map((row) => EffectTypeRow.fromJson(row)),
      json.group_name,
      json.columns,
      json.effect_groups,
      json.effect_types
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
  public static fromJson(json: DenovoReportJson | null): DenovoReport | null {
    if (!json) {
      return null;
    }
    return new DenovoReport(
      json.tables.map((table) => EffectTypeTable.fromJson(table))
    );
  }

  public constructor(
    public readonly tables: EffectTypeTable[]
  ) {}
}

export class VariantReport {
  public static fromJson(json: VariantReportJson): VariantReport {
    return new VariantReport(
      json.id,
      json.study_name,
      json.study_description,
      PeopleReport.fromJson(json.people_report),
      FamilyReport.fromJson(json.families_report, json.families),
      DenovoReport.fromJson(json.denovo_report)
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
  public static fromJson(json: LegendItemJson): LegendItem {
    return new LegendItem(json.id, json.name, json.color);
  }

  public constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly color: string
  ) {}
}

export class Legend {
  public static fromList(list: LegendItemJson[]): Legend {
    return new Legend(
      list.map((legendItem) => LegendItem.fromJson(legendItem))
    );
  }

  public constructor(
    public readonly legendItems: LegendItem[]
  ) {}
}
