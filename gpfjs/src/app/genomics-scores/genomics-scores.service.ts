import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions, URLSearchParams } from '@angular/http';
import { Observable } from 'rxjs';

import { MissenseScoresHistogramData } from './genomics-scores';
import { ConfigService } from '../config/config.service';

import 'rxjs/add/operator/map';

@Injectable()
export class MissenseScoresService {
  private missenseScoresUrl = 'missense_scores';

  constructor(
    private http: Http,
    private config: ConfigService
  ) { }

  getHistogramData(datasetId, scoreId): Observable<MissenseScoresHistogramData> {
    let options = new RequestOptions();
    options.search = new URLSearchParams();

    options.search.set('dataset_id', datasetId);
    options.search.set('score_id', scoreId);

    return this.http
      .get(this.missenseScoresUrl, options)
      .map(res => {
        return MissenseScoresHistogramData.fromJson(res.json());
      });
  }
}
