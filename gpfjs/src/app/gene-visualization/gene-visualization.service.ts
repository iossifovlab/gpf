import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class GeneVisualizationService {

  constructor() { }

  getCHD8() {
    const CHD8 = require('./CHD8.json');
    return CHD8;
  }
}
