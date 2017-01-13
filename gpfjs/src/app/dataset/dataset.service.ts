import { Injectable } from '@angular/core';
import { Headers, Http, Response } from '@angular/http';
import { Observable } from 'rxjs';

import 'rxjs/add/operator/toPromise';

import { IdDescription } from '../common/iddescription';
import { Phenotype } from '../phenotypes/phenotype';
import { Dataset } from '../dataset/dataset';
import { ConfigService } from '../config/config.service';


@Injectable()
export class DatasetService {
  private datasetUrl = 'dataset';
  private effecttypesUrl = 'effecttypes';

  private headers = new Headers({ 'Content-Type': 'application/json' });

  selectedDatasetId: string = 'ssc';

  constructor(
    private http: Http,
    private config: ConfigService
  ) { }

  private handleIdDescriptionError(error: any): IdDescription[] {
    console.error('error while parsing id/descriptions response: ', error);
    return <IdDescription[]>[];
  }

  private parseIdDescriptionResponse(response: Response): IdDescription[] {
    let data = response.json();
    if (data.data === undefined) {
      return <IdDescription[]>[];
    }
    let result: Object[] = data.data;
    if (typeof result === 'string') {
      result = JSON.parse(result);
    }

    let output: Array<IdDescription> = new Array<IdDescription>();
    for (let obj of result) {
      output.push(new IdDescription(obj['id'], obj['description']));
    }
    return output;
  }

  private getIdDescriptions(url: string): Promise<IdDescription[]> {
    return this.http.get(url)
      .toPromise()
      .then(this.parseIdDescriptionResponse)
      .catch(this.handleIdDescriptionError);
  }

  private handleStringsError(error: any): string[] {
    console.error('error while strings response: ', error);
    return [];
  }

  private parseStringsResponse(response: Response): string[] {
    let data = response.json();
    if (data.data === undefined) {
      return [];
    }
    let result: Object[] = data.data;
    if (typeof result === 'string') {
      result = JSON.parse(result);
    }
    let output = new Array<string>();
    for (let obj of result) {
      output.push(<string>(obj.valueOf()));
    }
    return output;
  }

  private getStrings(url: string): Promise<string[]> {
    return this.http.get(url)
      .toPromise()
      .then(this.parseStringsResponse)
      .catch(this.handleStringsError);
  }

  getDatasets(): Promise<IdDescription[]> {
    return this.getIdDescriptions(this.datasetUrl);
  }

  private parseDatasetResponse(response: Response): Dataset {
    let data = response.json();
    if (data.data === undefined) {
      return undefined;
    }
    let result: Object[] = data.data;
    if (typeof result === 'string') {
      result = JSON.parse(result);
    }
    return new Dataset(
      result['id'],
      result['description'],
      result['hasDenovo'],
      result['hasTransmitted'],
      result['hasCnv'],
      result['hasPhenoDb']
    );
  }

  private handleDatasetError(error: any): Dataset {
    console.error('error while parsing dataset response: ', error);
    return undefined;
  }

  getDataset(datasetId: string): Promise<Dataset> {
    let url = `${this.datasetUrl}/${datasetId}`;
    return this.http.get(url)
      .toPromise()
      .then(this.parseDatasetResponse)
      .catch(this.handleDatasetError);
  }

  private parsePhenotypesResponse(response: Response): Phenotype[] {
    let data = response.json();
    if (data.data === undefined) {
      return <Phenotype[]>[];
    }
    let result: Object[] = data.data;
    if (typeof result === 'string') {
      result = JSON.parse(result);
    }

    let output: Array<Phenotype> = new Array<Phenotype>();
    for (let obj of result) {
      let pheno = new Phenotype(
        obj['id'],
        obj['description'],
        obj['color']
      );
      output.push(pheno);
    }
    return output;
  }

  private handlePhenotypesError(error: any): Phenotype[] {
    console.error('error while parsing phenotypes response: ', error);
    return <Phenotype[]>[];
  }

  getPhenotypes(datasetId: string): Promise<Phenotype[]> {
    let url = `${this.datasetUrl}/${datasetId}/phenotypes`;
    return this.http.get(url)
      .toPromise()
      .then(this.parsePhenotypesResponse)
      .catch(this.handlePhenotypesError);
  }

  getStudytypes(datasetId: string): Promise<IdDescription[]> {
    let url = `${this.datasetUrl}/${datasetId}/studytypes`;
    return this.getIdDescriptions(url);
  }

  getEffecttypesGroups(): Promise<IdDescription[]> {
    let url = `${this.effecttypesUrl}/group`;
    return this.getIdDescriptions(url);
  }

  getEffecttypesInGroup(groupId: string): Promise<string[]> {
    let url = `${this.effecttypesUrl}/group/${groupId}`;
    return this.getStrings(url);
  }

  getEffecttypesGroupsColumns(datasetId: string): Promise<IdDescription[]> {
    let url = `${this.effecttypesUrl}/dataset/${datasetId}/columns`;
    return this.getIdDescriptions(url);
  }

  getEffecttypesGroupsButtons(datasetId: string): Promise<IdDescription[]> {
    let url = `${this.effecttypesUrl}/dataset/${datasetId}/buttons`;
    return this.getIdDescriptions(url);
  }

}
