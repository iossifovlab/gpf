import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

@Injectable()
export class ConfigService {
  public readonly rootUrl: string = environment.basePath;
  public readonly baseUrl: string = environment.apiPath;
}
