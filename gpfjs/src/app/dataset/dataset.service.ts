import { Injectable } from '@angular/core';
import { Headers, Http, Response } from '@angular/http';
import { Observable } from 'rxjs';

import 'rxjs/add/operator/toPromise';

import { Dataset, IdDescription, Phenotype } from './dataset';

@Injectable()
export class DatasetService {
  private datasetUrl = 'dataset';
  private headers = new Headers({ 'Content-Type': 'application/json' });

  constructor(
    private http: Http
  ) { }

  private handleIdDescriptionError(error: any): IdDescription[] {
    console.error('error while parsing id/descriptions response: ', error);
    return <IdDescription[]>[];
  }

  private parseIdDescriptionResponse(response: Response): IdDescription[] {
    let data = response.json();
    if (data.result === undefined) {
      return <IdDescription[]>[];
    }
    let result: Object[] = JSON.parse(data.result);

    let output: Array<IdDescription> = new Array<IdDescription>();
    for (let obj of result) {
      output.push(new IdDescription(obj['id'], obj['description']));
    }
    return output;
  }

  getDatasets(): Promise<IdDescription[]> {
    return this.http.get(this.datasetUrl)
      .toPromise()
      .then(this.parseIdDescriptionResponse)
      .catch(this.handleIdDescriptionError);
  }

  private parseDatasetResponse(response: Response): Dataset {
    let data = response.json();
    if (data.result === undefined) {
      return undefined;
    }
    let result: Object = JSON.parse(data.result);
    return new Dataset(
      result['id'],
      result['description'],
      result['hasDenovo'],
      result['hasTransmitted'],
      result['hasCnv']
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
    if (data.result === undefined) {
      return <Phenotype[]>[];
    }
    let result: Object[] = JSON.parse(data.result);

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
    let url = `${this.datasetUrl}/${datasetId}/phenotype`;
    return this.http.get(url)
      .toPromise()
      .then(this.parsePhenotypesResponse)
      .catch(this.handlePhenotypesError);
  }
}
