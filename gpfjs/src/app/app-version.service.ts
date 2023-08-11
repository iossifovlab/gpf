import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { ConfigService } from './config/config.service';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class AppVersionService {
  public constructor(
    private http: HttpClient,
    private config: ConfigService) { }

  public getGpfVersion(): Observable<string> {
    return this.http.get<{version: string}>(this.config.baseUrl + 'version').pipe(
      map(json => json.version)
    );
  }
}
