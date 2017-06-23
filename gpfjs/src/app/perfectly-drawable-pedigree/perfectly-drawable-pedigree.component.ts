import { Component, OnInit, ChangeDetectionStrategy } from '@angular/core';

import { PedigreeData } from '../genotype-preview-table/genotype-preview';
import { PedigreeMockService } from './pedigree-mock.service';
import { Individual, MatingUnit, IndividualSet, ParentalUnit } from '../pedigree-chart/pedigree-data';
import {
  hasIntersection, intersection, equal, isSubset, difference
} from '../utils/sets-helper';

import { SandwichInstance, solveSandwich, Interval } from '../utils/interval-sandwich';
import { PerfectlyDrawablePedigreeService } from './perfectly-drawable-pedigree.service';

@Component({
  selector: 'gpf-perfectly-drawable-pedigree',
  templateUrl: './perfectly-drawable-pedigree.component.html',
  styleUrls: ['./perfectly-drawable-pedigree.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [PerfectlyDrawablePedigreeService]
})
export class PerfectlyDrawablePedigreeComponent implements OnInit {

  private families: {};
  private drawInput = true;

  constructor(
    private pedigreeMockService: PedigreeMockService,
    private perfectlyDrawablePedigreeService: PerfectlyDrawablePedigreeService
  ) { }

  getMaxMatingUnitsPerIndividual(familyId: string) {
    let si = this.perfectlyDrawablePedigreeService
      .createSandwichInstance(this.families[familyId]);

    let matingUnits = si.vertices.filter(v => v instanceof MatingUnit) as MatingUnit[];
    let fathersArray = matingUnits.map(mu => mu.father);
    let mothersArray = matingUnits.map(mu => mu.mother);

    let maxMatings = Math.max(
      fathersArray.length - (new Set(fathersArray)).size + 1,
      mothersArray.length - (new Set(mothersArray)).size + 1);

    return maxMatings;
  }

  ngOnInit() {
    this.families = this.pedigreeMockService.getMockFamily();
    let allFamilies = [];
    for (let familyId in this.families) {
      if (this.families.hasOwnProperty(familyId)) {
        allFamilies.push(familyId);
      }
    }

    if (this.drawInput) {
      let maxMatings = 0;
      let moreThanTwoMatingsFamilies = [];
      for (let familyId of this.newNotPDP) {
        let currentMaxMatings = this.getMaxMatingUnitsPerIndividual(familyId);

        if (currentMaxMatings >= maxMatings) {
          console.log('Max matings of family', familyId, 'is', currentMaxMatings);
          maxMatings = currentMaxMatings;
        }
        if (currentMaxMatings > 2) {
          moreThanTwoMatingsFamilies.push(familyId);
        }
        // if (fathersArray.length === (new Set(fathersArray)).size &&
        //     mothersArray.length === (new Set(mothersArray)).size) {
        //   console.log('family ', familyId, 'has only sinly mated individuals');
        // }
      }
      console.log('moreThanTwoMatingsFamilies', moreThanTwoMatingsFamilies);

      console.log('left:', Array.from(difference(new Set(this.newNotPDP), new Set(moreThanTwoMatingsFamilies))));

      let otherFamilies = difference(new Set(allFamilies), new Set(this.newNotPDP));
      for (let familyId of Array.from(otherFamilies)) {
        if (this.getMaxMatingUnitsPerIndividual(familyId) > 1) {
          console.log('Family', familyId, 'has more than 1 mating per individual');
        }
      }

      let [sandwichInstance, isPDP] = this.perfectlyDrawablePedigreeService
        .isPDP(this.families['AU1433']);


    } else {
      this.areAllPDP();
    }
  }

  newNotPDP = ['AU0025', 'AU0110', 'AU0768', 'AU0931', 'AU0932', 'AU0985', 'AU1025', 'AU1245', 'AU1271', 'AU1373', 'AU1410', 'AU1500', 'AU1607', 'AU1608', 'AU1616', 'AU1619', 'AU1689', 'AU1921', 'AU1940', 'AU1952', 'AU1961', 'AU2136', 'AU2311', 'AU2720', 'AU2756', 'AU2837', 'AU2860', 'AU3344', 'AU3541', 'AU3618', 'AU3702', 'AU3766', 'AU3872', 'AU3889', 'AU3939', 'AU3973', 'AU4001', 'AU4033', 'AU4058', 'AU4138', 'AU4141'];
  oldNotPDP = ['AU0025', 'AU0110', 'AU0455', 'AU0668', 'AU0768', 'AU0931', 'AU0932', 'AU0985', 'AU1025', 'AU1245', 'AU1271', 'AU1373', 'AU1410', 'AU1500', 'AU1607', 'AU1608', 'AU1616', 'AU1619', 'AU1689', 'AU1921', 'AU1940', 'AU1952', 'AU1961', 'AU2136', 'AU2311', 'AU2720', 'AU2756', 'AU2837', 'AU2860', 'AU3344', 'AU3541', 'AU3618', 'AU3702', 'AU3766', 'AU3872', 'AU3889', 'AU3939', 'AU3973', 'AU4001', 'AU4033', 'AU4058', 'AU4138', 'AU4141'];
  areAllPDP() {

    // console.log(subtract(new Set(this.oldNotPDP), new Set(this.newNotPDP)));
    console.log('Beginning!');
    let counter = 0;
    let notPDP = [];
    let times = [];
    let succeededTimes = [];
    for (let familyId in this.families) {
      if (this.families.hasOwnProperty(familyId)) {
        let start = Date.now()
        let [sandwichInstance, isPDP] = this.perfectlyDrawablePedigreeService
          .isPDP(this.families[familyId]);
        let time = start - Date.now();
        times.push([time, !!isPDP]);
        if (!isPDP) {
          // console.log('Found not perfectly drawable:');
          notPDP.push(familyId);
        } else {
          succeededTimes.push(time)
        }
        if ((counter++) % 1 === 0) {
          console.log('on family', familyId);
        }
      }
    }
    console.log('Not pdp:', notPDP);
    console.log('Times:', times.map(([time, ]) => time));
    console.log('Mean time:', times.map(a => a[0]).reduce((a, b) => a + b, 0) / times.length);
    console.log('succeeded times', succeededTimes);
    console.log('succeeded mean time', succeededTimes.reduce((a, b) => a+b, 0) / succeededTimes.length);
  }


}
