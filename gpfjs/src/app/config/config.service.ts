import { Injectable } from '@angular/core';

@Injectable()
export class ConfigService {

  // Drakov default url
  readonly baseUrl: string = 'http://localhost:3000';

  constructor() { }



}
