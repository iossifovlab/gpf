import { Injectable } from '@angular/core';
import { Http, Response } from '@angular/http';

import { Observable } from 'rxjs';

import { StudiesSummaries } from './studies-summaries';

@Injectable()
export class StudiesSummariesService {
    private apiUrl = 'common_reports/studies_summaries';

    constructor(
      private http: Http
    ) {}

    getStudiesSummaries(): Observable<StudiesSummaries> {
      return this.http
        .get(this.apiUrl)
        .map(response => response.json())
        .map(
          jsonStudiesSummaries =>
            StudiesSummaries.fromJsonArray(jsonStudiesSummaries)
        )
        .catch(error => {
          console.log(error);
          return Observable.of(null as StudiesSummaries);
        });
    }

}
