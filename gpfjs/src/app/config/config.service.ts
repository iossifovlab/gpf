import { Injectable } from '@angular/core';

@Injectable()
export class ConfigService {

  readonly baseUrl: string = 'http://localhost:8000/api/v3/';
  // Drakov default url
  // readonly baseUrl: string = 'http://localhost:3000';

  constructor() { }



}
