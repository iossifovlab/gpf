import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { ConfigService } from './config/config.service';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class InstanceService {
  private http = inject(HttpClient);
  private config = inject(ConfigService);

  private readonly instanceUrl = 'instance';
  // eslint-disable-next-line @typescript-eslint/naming-convention
  private readonly headers = new HttpHeaders({ 'Content-Type': 'application/json' });

  public getGpfVersion(): Observable<string> {
    return this.http.get<{version: string}>(`${this.config.baseUrl}${this.instanceUrl}/version`).pipe(
      map(json => json.version)
    );
  }

  public getGenome(): Observable<string> {
    return this.http.get<{build: string}>(`${this.config.baseUrl}${this.instanceUrl}/genome`).pipe(
      map(json => json.build)
    );
  }

  public writeHomeDescription(description: string): Observable<object> {
    const options = { headers: this.headers, withCredentials: true };
    return this.http.post(
      `${this.config.baseUrl}${this.instanceUrl}/description`,
      {content: description},
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
      {content: description},
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

  public getFeatureFlags(): Observable<object> {
    const options = { headers: this.headers, withCredentials: true };
    return this.http.get(
      `${this.config.baseUrl}${this.instanceUrl}/features`,
      options
    );
  }
}
