import { Component, OnInit } from '@angular/core';

import { PedigreeMockService
} from '../perfectly-drawable-pedigree/pedigree-mock.service';
import { PerfectlyDrawablePedigreeService
} from '../perfectly-drawable-pedigree/perfectly-drawable-pedigree.service';
import { difference } from '../utils/sets-helper';

@Component({
  selector: 'gpf-non-pdp-pedigrees',
  templateUrl: './non-pdp-pedigrees.component.html',
  styleUrls: ['./non-pdp-pedigrees.component.css'],
  providers: [PerfectlyDrawablePedigreeService]
})
export class NonPdpPedigreesComponent implements OnInit {

  families: {};
  familyKeys: string[];

  nonPDP = [
    'AU0931', 'AU0932', 'AU0985',
    'AU1025', 'AU1271', 'AU1373', 'AU1410', 'AU1500',
    'AU1607', 'AU1608', 'AU1619', 'AU1689',
    'AU1940', 'AU1952', 'AU1961', 'AU2136', 'AU2311', 'AU2720',
    'AU2756', 'AU2837', 'AU2860', 'AU3344', 'AU3541', 'AU3618',
    'AU3702', 'AU3766', 'AU3872', 'AU3889', 'AU3939', 'AU3973',
    'AU4001', 'AU4033', 'AU4058', 'AU4138', 'AU4141'
  ];

  maybePDP = ['AU0025', 'AU0110', 'AU0768', 'AU1245', 'AU1616', 'AU1921'];

  constructor(
    private pedigreeMockService: PedigreeMockService,
    private perfectlyDrawablePedigreeService: PerfectlyDrawablePedigreeService
  ) { }


  ngOnInit() {
    this.families = this.pedigreeMockService.getMockFamily();
    this.familyKeys = [];
    for (let familyName in this.families) {
      if (this.families.hasOwnProperty(familyName)) {
        this.familyKeys.push(familyName);
      }
    }


    this.familyKeys = this.filterSimple(this.familyKeys);
    // this.familyKeys = this.familyKeys.slice(0, 400);
    this.familyKeys = Array.from(difference(difference(new Set(this.familyKeys), new Set(this.nonPDP)), new Set(this.maybePDP)));
    // this.familyKeys = ["AU0008"];
  }

    filterSimple(familyKeys: string[]) {
        return familyKeys.filter(familyKey => {
            let family = this.families[familyKey];
            let matingUnits = new Set<string>();
            for (let member of family) {
                matingUnits.add(`${member.father};${member.mother}`);
            }

            return matingUnits.size > 2;
          });
      }

}
