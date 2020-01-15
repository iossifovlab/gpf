import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

@Injectable()
export class ConfigService {
  readonly baseUrl: string = environment.apiPath;
  // Drakov default url
  // readonly baseUrl: string = 'http://localhost:3000';

  constructor() { }
}
