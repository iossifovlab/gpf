import { Component, OnInit } from '@angular/core';
import { PedigreeMockService } from '../perfectly-drawable-pedigree/pedigree-mock.service';
import { PerfectlyDrawablePedigreeService } from '../perfectly-drawable-pedigree/perfectly-drawable-pedigree.service';

@Component({
  selector: 'gpf-non-pdp-pedigrees',
  templateUrl: './non-pdp-pedigrees.component.html',
  styleUrls: ['./non-pdp-pedigrees.component.css'],
  providers: [PerfectlyDrawablePedigreeService],
  standalone: false
})
export class NonPdpPedigreesComponent implements OnInit {
  public families: object;
  public familyKeys: string[];

  public constructor(
    private pedigreeMockService: PedigreeMockService,
  ) { }

  public ngOnInit(): void {
    this.families = this.pedigreeMockService.getMockFamily();
    this.familyKeys = [];
    for (const familyName in this.families) {
      if (this.families.hasOwnProperty(familyName)) {
        this.familyKeys.push(familyName);
      }
    }
  }

  public filterSimple(familyKeys: string[]): string[] {
    return familyKeys.filter(familyKey => {
      const family = this.families[familyKey];
      const matingUnits = new Set<string>();
      for (const member of family) {
        matingUnits.add(`${member.father};${member.mother}`);
      }
      return matingUnits.size > 2;
    });
  }
}
