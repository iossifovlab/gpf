import { IdDescription } from '../common/iddescription';
import { IdName } from '../common/idname';


export class SelectorValue extends IdName {
  constructor(
    readonly id: string,
    readonly name: string,
    readonly color: string,
  ) {
    super(id, name);
  }
}

export class PedigreeSelector extends IdName {
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
