import { Injectable } from '@angular/core';
import { PedigreeData } from '../genotype-preview-model/genotype-preview';

@Injectable()
export class PedigreeMockService {

  complexFamily = [
    ['AU0052', '4', '0', '0', '1', '', 'AU005204', 'asd'],
    ['AU0052', '5', '101', '102', '2', '', 'AU005205', 'asd'],
    ['AU0052', '13', '4', '5', '1', 'Autism', 'AU005213', 'asd'],
    ['AU0052', '14', '4', '5', '1', 'Autism', 'AU005214', 'asd'],
    ['AU0052', '15', '4', '5', '1', 'Autism', 'AU005215', 'asd'],
    ['AU0052', '19', '4', '5', '1', '', 'AU005219', 'asd'],
    ['AU0052', '101', '0', '0', '1', '', 'AU0052101', 'asd'],
    ['AU0052', '102', '0', '0', '2', '', 'AU0052102', 'asd'],
    ['AU0052', '211', '101', '102', '1', '', 'AU0052211', 'asd'],
    ['AU0052', '212', '0', '0', '2', '', 'AU0052212', 'asd'],
    ['AU0052', '311', '211', '212', '1', '', 'AU0052311', 'asd'],
    ['AU0052', '312', '211', '212', '1', 'Autism', 'AU0052312', 'asd'],
    ['AU0052', '313', '211', '212', '2', '', 'AU0052313', 'asd'],
    ['AU0052', '314', '211', '212', '1', '', 'AU0052314', 'asd'],
  ].map(person => PedigreeData.fromArray(person));

  simpleFamily = [
    ['AU0052', '211', '0', '0', '1', '', 'AU0052211', 'asd'],
    ['AU0052', '212', '0', '0', '2', '', 'AU0052212', 'asd'],
    ['AU0052', '311', '211', '212', '1', '', 'AU0052311', 'asd'],
    ['AU0052', '312', '211', '212', '1', 'Autism', 'AU0052312', 'asd'],
    ['AU0052', '313', '211', '212', '2', '', 'AU0052313', 'asd'],
    ['AU0052', '314', '211', '212', '1', '', 'AU0052314', 'asd'],
  ].map(person => PedigreeData.fromArray(person));

  simplestFamily = [
    ['AU0052', '211', '0', '0', '1', '', 'AU0052211', 'asd'],
    ['AU0052', '212', '0', '0', '2', '', 'AU0052212', 'asd'],
    ['AU0052', '311', '211', '212', '1', '', 'AU0052311', 'asd'],
  ].map(person => PedigreeData.fromArray(person));

  processAllFamilies() {
    return this.allFamilies.split('\n')
      .map(arr => {
        let result = arr.split(',');
        result.pop();
        return result;
      })
      .map(person => {
        person[5] = '#ffffff';

        person[6] = '';
        person[4] = (person[4] === '1') ? 'F' : 'M';
        return person;
      })
      .map(person => PedigreeData.fromArray(person))
      .reduce((acc, person) => {
        if (acc[person.pedigreeIdentifier]) {
          acc[person.pedigreeIdentifier].push(person);
        } else {
          acc[person.pedigreeIdentifier] = [person];
        }
        return acc;
      }, {});
  }

  getMockFamily(): {} {
    return this.processAllFamilies();
  }
  // truncated
  allFamilies = `AU0001,1,0,0,2,,AU000101,,
AU0001,2,0,0,1,,AU000102,,
AU0001,3,2,1,2,Autism,AU000103,,
AU0001,4,2,1,2,Autism,AU000104,,
AU0001,5,2,1,2,Autism,AU000105,,
AU0001,6,2,1,2,Autism,AU000106,,`

}
