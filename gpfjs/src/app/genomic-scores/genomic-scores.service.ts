import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions, URLSearchParams } from '@angular/http';
import { Observable } from 'rxjs';

import { GenomicScoresHistogramData } from './genomic-scores';
import { ConfigService } from '../config/config.service';

import 'rxjs/add/operator/map';

@Injectable()
export class GenomicScoresService {
  private genomicScoresUrl = 'missense_scores';

  constructor(
    private http: Http,
    private config: ConfigService
  ) { }

  getHistogramData(datasetId, scoreId): Observable<GenomicScoresHistogramData> {
    let options = new RequestOptions();
    options.search = new URLSearchParams();

    options.search.set('dataset_id', datasetId);
    options.search.set('score_id', scoreId);

    return this.http
      .get(this.genomicScoresUrl, options)
      .map(res => {
        return GenomicScoresHistogramData.fromJson(res.json());
      });
  }
}
