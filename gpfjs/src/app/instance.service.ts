import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { ConfigService } from './config/config.service';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class InstanceService {
  private readonly instanceUrl = 'instance';
  // eslint-disable-next-line @typescript-eslint/naming-convention
  private readonly headers = new HttpHeaders({ 'Content-Type': 'application/json' });

  public constructor(
    private http: HttpClient,
    private config: ConfigService) { }

  public getGpfVersion(): Observable<string> {
    return this.http.get<{version: string}>(`${this.config.baseUrl}${this.instanceUrl}/version`).pipe(
      map(json => json.version)
    );
  }

  public writeHomeDescription(description: string): Observable<object> {
    const options = { headers: this.headers, withCredentials: true };
    return this.http.post(
      `${this.config.baseUrl}${this.instanceUrl}/description`,
      {description: description},
      options
    );
  }

  public getHomeDescription(): Observable<object> {
    const options = { headers: this.headers, withCredentials: true };
    return this.http.get(
      `${this.config.baseUrl}${this.instanceUrl}/description`,
      options
    );
  }

  public writeAboutDescription(description: string): Observable<object> {
    const options = { headers: this.headers, withCredentials: true };
    return this.http.post(
      `${this.config.baseUrl}${this.instanceUrl}/about`,
      {description: description},
      options
    );
  }

  public getAboutDescription(): Observable<object> {
    const options = { headers: this.headers, withCredentials: true };
    return this.http.get(
      `${this.config.baseUrl}${this.instanceUrl}/about`,
      options
    );
  }
}
