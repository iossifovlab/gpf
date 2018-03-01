import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
import { Observable } from 'rxjs';

import 'rxjs/add/operator/toPromise';

import { ConfigService } from '../config/config.service';
import { GenotypePreview, GenotypePreviewsArray } from '../genotype-preview-model/genotype-preview';
import { QueryData } from './query';



@Injectable()
export class QueryService {
  private genotypePreviewUrl = 'genotype_browser/preview';

  private headers = new Headers({ 'Content-Type': 'application/json' });

  constructor(
    private http: Http,
    private config: ConfigService
  ) {
  }

  private parseGenotypePreviewResponse(response: Response): GenotypePreviewsArray {
    let data = response.json();
    let genotypePreviewsArray = GenotypePreviewsArray.fromJson(data);
    return genotypePreviewsArray;
  }

  getGenotypePreviewByFilter(filter: QueryData): Observable<GenotypePreviewsArray> {
    let options = new RequestOptions({
      headers: this.headers, withCredentials: true
    });

    return this.http.post(this.genotypePreviewUrl, filter, options)
      .map(this.parseGenotypePreviewResponse);
  }
}
