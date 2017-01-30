import { IdDescription } from '../common/iddescription';
import { IdName } from '../common/idname';


export class SelectorValue extends IdName {
  static fromJson(json: any): SelectorValue {
    return new SelectorValue(
      json['id'],
      json['name'],
      json['color'],
    );
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<SelectorValue> {
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
    return new PedigreeSelector(
      json['id'],
      json['name'],
      json['souce'],
      SelectorValue.fromJson(json['defaultValue']),
      SelectorValue.fromJsonArray(json['domain']),
    );
  }
  static fromJsonArray(jsonArray: Array<Object>): Array<PedigreeSelector> {
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

export class GenotypeBrowser {
  static fromJson(json: any): GenotypeBrowser {
    return new GenotypeBrowser(
      json['hasDenovo'],
      json['hasCNV'],
      json['hasAdvancedFamilyFilters'],
      json['hasTransmitted'],
      json['hasPedigreeSelector'],
      json['hasStudyTypes'],
      json['mainForm']
    );
  }

  constructor(
    readonly hasDenovo: boolean,
    readonly hasCNV: boolean,
    readonly hasAdvancedFamilyFilters: boolean,
    readonly hasTransmitted: boolean,
    readonly hasPedigreeSelector: boolean,
    readonly hasStudyTypes: boolean,
    readonly mainForm: string
  ) {

  }
}

export class Dataset extends IdName {
  static fromJson(json: any): Dataset {
    return new Dataset(
      json['id'],
      json['name'],
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
    return jsonArray.map((json) => Dataset.fromJson(json));
  }


  constructor(
    readonly id: string,
    readonly name: string,
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
