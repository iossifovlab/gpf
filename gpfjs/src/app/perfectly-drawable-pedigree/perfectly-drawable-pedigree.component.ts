import { Component, OnInit, Input } from '@angular/core';

import { Observable, BehaviorSubject } from 'rxjs';

import { PedigreeData } from '../genotype-preview-table/genotype-preview';
import { Individual, MatingUnitWithIntervals, IndividualSet, ParentalUnit, IndividualWithPosition } from '../pedigree-chart/pedigree-data';
import {
  hasIntersection, intersection, equal, isSubset, difference
} from '../utils/sets-helper';

import { SandwichInstance, solveSandwich, IntervalForVertex } from '../utils/interval-sandwich';
import { PerfectlyDrawablePedigreeService } from './perfectly-drawable-pedigree.service';

@Component({
  selector: 'gpf-perfectly-drawable-pedigree',
  templateUrl: './perfectly-drawable-pedigree.component.html',
  styleUrls: ['./perfectly-drawable-pedigree.component.css'],
})
export class PerfectlyDrawablePedigreeComponent {






    // let maxRank = intervals.reduce((acc, i) => Math.max(acc, i.vertex.rank), 0);
    //
    // return intervals
    //   .map(i => [i.left, -(i.vertex.rank - maxRank) * yGap] as [number, number]);



}
