import { Type, plainToClass } from 'class-transformer';
import 'reflect-metadata';
import * as YAML from 'yaml';

import { GenesBlockPage } from './genes-block-page';
import { EnrichmentModelsBockPage } from './enrichment-models-block-page';
import { GeneScoresPage } from './gene-scores-page';

export class EnrichmentToolData {
  public name: string;
  public study: string;
  public target: string;

  @Type(() => Case)
  public cases: Case[];
}

class Case {
  public name: string;

  @Type(() => Params)
  public params: Params;

  @Type(() => Expected)
  public expected: Expected[];
}

class Expected {
  public rowId: string;
  public values: string[];
}

export class Params {
  public geneSymbols: string[];

  @Type(() => Models)
  public models: Models;

  @Type(() => GeneWeight)
  public geneScore: GeneWeight;

  @Type(() => GeneSet)
  public geneSet: GeneSet;
}

class Models {
  public backgroundModel: string;
  public countingModel: string;
}

class GeneWeight {
  public id: string;
  public from: number;
  public to: number;
}

class GeneSet {
  public id: string

  @Type(() => GeneSetCollection)
  public collection: GeneSetCollection;
}

class GeneSetCollection {
  public id: string;

  @Type(() => GeneSetCollectionAffectedStatus)
  public affectedStatus: GeneSetCollectionAffectedStatus[];
}

class GeneSetCollectionAffectedStatus {
  public studyId: string;
  public affected: boolean;
  public unaffected: boolean
}

// Pass path to yaml file using the '--env' flag in the cypress command:
// npx cypress open --config baseUrl=http://172.20.0.5/gpf/ --env yamlPath=cypress/iossifov.data.expected.yaml
export function parseYamlData(filePath: string): EnrichmentToolData[] {
  if (filePath === undefined) {
    return;
  }

  return plainToClass(EnrichmentToolData, YAML.parse(filePath) as EnrichmentToolData[]);
}

export function applyData(params: Params): void {
  const genesBlockPage = new GenesBlockPage();
  const geneScoresPage = new GeneScoresPage();
  const enrichmentModelsBockPage = new EnrichmentModelsBockPage();

  if (params.geneSymbols) {
    genesBlockPage.geneSymbolsButton.click();
    genesBlockPage.geneSymbolsTextarea.clear().type(params.geneSymbols.join(','));
  } else if (params.geneSet) {
    genesBlockPage.geneSetsButton.click();

    genesBlockPage.geneSetsCollectionSelectorDropdownMenu.select(params.geneSet.collection.id, {force: true});

    genesBlockPage.geneSetsSearchbox.click();
    genesBlockPage.geneSetsSearchbox.type(params.geneSet.id);
    genesBlockPage.findGeneSetsSearchboxDropdownOptionsByText(params.geneSet.id).click();

    if (params.geneSet.collection.id === 'Denovo' && params.geneSet.collection.affectedStatus) {
      // TODO
    }
  } else if (params.geneScore) {
    genesBlockPage.geneScoresButton.click();
    geneScoresPage.dropdownButton.select(params.geneScore.id);

    if (params.geneScore.from) {
      geneScoresPage.fromInputField.clear();
      geneScoresPage.fromInputField.type(params.geneScore.from.toString());
      cy.wait(3000); // wait needed for https://github.com/iossifovlab/gpfjs/issues/844
    }

    if (params.geneScore.to) {
      geneScoresPage.fromInputField.clear();
      geneScoresPage.fromInputField.type(params.geneScore.to.toString());
      cy.wait(3000); // wait needed for https://github.com/iossifovlab/gpfjs/issues/844
    }
  }

  if (params.models) {
    enrichmentModelsBockPage.selectModelsButton.click();

    if (params.models.backgroundModel) {
      enrichmentModelsBockPage.backgroundModelsDropdown.select(params.models.backgroundModel);
    }

    if (params.models.countingModel) {
      enrichmentModelsBockPage.countingModelsDropdown.select(params.models.countingModel);
    }
  }
}