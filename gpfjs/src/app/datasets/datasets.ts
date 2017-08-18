import { IdDescription } from '../common/iddescription';
import { IdName } from '../common/idname';


export class SelectorValue extends IdName {
  static fromJson(json: any): SelectorValue {
    if (!json) {
      return undefined;
    }

    return new SelectorValue(
      json['id'],
      json['name'],
      json['color'],
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<SelectorValue> {
    if (!jsonArray) {
      return undefined;
    }
    return jsonArray.map((json) => SelectorValue.fromJson(json));
  }

  constructor(
    readonly id: string,
    readonly name: string,
    readonly color: string,
  ) {
    super(id, name);
  }
}

export class PedigreeSelector extends IdName {
  static fromJson(json: any): PedigreeSelector {
    if (!json) {
      return undefined;
    }

    return new PedigreeSelector(
      json['id'],
      json['name'],
      json['souce'],
      SelectorValue.fromJson(json['defaultValue']),
      SelectorValue.fromJsonArray(json['domain']),
    );
  }
  static fromJsonArray(jsonArray: Array<Object>): Array<PedigreeSelector> {
    if (!jsonArray) {
      return undefined;
    }

    return jsonArray.map((json) => PedigreeSelector.fromJson(json));
  }

  constructor(
    readonly id: string,
    readonly name: string,
    readonly source: string,
    readonly defaultValue: SelectorValue,
    readonly domain: SelectorValue[]
  ) {
    super(id, name);
  }
}

export class AdditionalColumnSlot {
  static fromJson(json: any): AdditionalColumnSlot {
    return new AdditionalColumnSlot(
      json['id'],
      json['name']
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<AdditionalColumnSlot> {
    if (!jsonArray) {
      return undefined;
    }
    return jsonArray.map((json) => AdditionalColumnSlot.fromJson(json));
  }

  constructor(
    readonly id: string,
    readonly name: string,
  ) {}
}

export class AdditionalColumn {
  static fromJson(json: any): AdditionalColumn {
    return new AdditionalColumn(
      json['name'],
      AdditionalColumnSlot.fromJsonArray(json['slots']),
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<AdditionalColumn> {
    if (!jsonArray) {
      return [];
    }
    return jsonArray.map((json) => AdditionalColumn.fromJson(json));
  }

  constructor(
    readonly name: string,
    readonly slots: Array<AdditionalColumnSlot>
  ) {}
}

export class MeasureFilter {
  static fromJson(json: any): MeasureFilter {
    return new MeasureFilter(
      json['role'],
      json['filterType'],
      json['measure'],
      json['domain']
    );
  }

  constructor(
    readonly role: string,
    readonly filterType: string,
    readonly measure: string,
    readonly domain: Array<string>
  ) {}
}

export class PhenoFilter {
  static fromJson(json: any): PhenoFilter {
    return new PhenoFilter(
      json['name'],
      json['measureType'],
      MeasureFilter.fromJson(json['measureFilter']),
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<PhenoFilter> {
    if (!jsonArray) {
      return undefined;
    }
    return jsonArray.map((json) => PhenoFilter.fromJson(json));
  }

  constructor(
    readonly name: string,
    readonly measureType: string,
    readonly measureFilter: MeasureFilter
  ) {}
}

export class GenotypeBrowser {
  static fromJson(json: any): GenotypeBrowser {
    return new GenotypeBrowser(
      json['hasPedigreeSelector'],
      json['hasPresentInChild'],
      json['hasPresentInParent'],
      json['hasCNV'],
      json['hasFamilyFilters'],
      json['hasStudyTypes'],
      json['mainForm'],
      [...AdditionalColumn.fromJsonArray(json['phenoColumns']),
       ...AdditionalColumn.fromJsonArray(json['genotypeColumns'])],
      PhenoFilter.fromJsonArray(json['phenoFilters']),
      PhenoFilter.fromJsonArray(json['familyStudyFilters'])
    );
  }

  constructor(
    readonly hasPedigreeSelector: boolean,
    readonly hasPresentInChild: boolean,
    readonly hasPresentInParent: boolean,
    readonly hasCNV: boolean,
    readonly hasFamilyFilters: boolean,
    readonly hasStudyTypes: boolean,
    readonly mainForm: string,
    readonly additionalColumns: Array<AdditionalColumn>,
    readonly phenoFilters: Array<PhenoFilter>,
    readonly familyStudyFilters: Array<PhenoFilter>,
  ) {

  }
}

export class Dataset extends IdName {
  static fromJson(json: any): Dataset {
    if (!json) {
      return undefined;
    }
    return new Dataset(
      json['id'],
      json['description'],
      json['name'],
      json['accessRights'],
      json['studies'],
      json['studyTypes'],
      json['phenoDB'],
      json['phenotypeGenotypeTool'],
      json['enrichmentTool'],
      json['phenotypeBrowser'],
      GenotypeBrowser.fromJson(json['genotypeBrowser']),
      PedigreeSelector.fromJsonArray(json['pedigreeSelectors']),
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<Dataset> {
    if (!jsonArray) {
      return undefined;
    }
    return jsonArray.map((json) => Dataset.fromJson(json));
  }


  constructor(
    readonly id: string,
    readonly description: string,
    readonly name: string,
    readonly accessRights: boolean,
    readonly studies: string[],
    readonly studyTypes: string[],
    readonly phenoDB: string,
    readonly phenotypeGenotypeTool: boolean,
    readonly enrichmentTool: boolean,
    readonly phenotypeBrowser: boolean,
    readonly genotypeBrowser: GenotypeBrowser,
    readonly pedigreeSelectors: PedigreeSelector[],
  ) {
    super(id, name);
  }
}


export interface DatasetsState {
  selectedDataset: Dataset;
  datasets: Dataset[];
};

const initialDatasetState = {
  selectedDataset: undefined,
  datasets: undefined
};

export const DATASETS_INIT = 'DATASETS_INIT';
export const DATASETS_SELECT = 'DATASETS_SELECT';

export function datasetsReducer(state: DatasetsState = initialDatasetState, action) {
  switch (action.type) {
    case DATASETS_INIT:
      return {
        datasets: action.payload,
        selectedDataset: null
      };
    case DATASETS_SELECT:
      return {
        datasets: state.datasets,
        selectedDataset: action.payload
      };
    default:
      return state;
  }
}
