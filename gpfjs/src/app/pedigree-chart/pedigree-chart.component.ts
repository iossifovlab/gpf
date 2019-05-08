import { Input, Component, OnInit, ChangeDetectionStrategy,  AfterViewInit, ViewChild, ChangeDetectorRef, OnDestroy } from '@angular/core';

// tslint:disable-next-line:import-blacklist
import { Observable, BehaviorSubject, Subject, Subscription } from 'rxjs';
// tslint:disable-next-line:import-blacklist
import 'rxjs/Rx';
import { difference } from '../utils/sets-helper';

import { IntervalForVertex } from '../utils/interval-sandwich';
import { PedigreeData } from '../genotype-preview-model/genotype-preview';
import {
  PerfectlyDrawablePedigreeService
} from '../perfectly-drawable-pedigree/perfectly-drawable-pedigree.service';

import { IndividualWithPosition, Line, IndividualSet, Individual, MatingUnit } from './pedigree-data';
import { ResizeService } from '../table/resize.service';

type OrderedIndividuals = Array<Individual>;

@Component({
  selector: 'gpf-pedigree-chart',
  templateUrl: './pedigree-chart.component.html',
  styleUrls: ['./pedigree-chart.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class PedigreeChartComponent implements OnInit, AfterViewInit, OnDestroy {

  static miximizedChart = new Subject<PedigreeChartComponent>();

  pedigreeDataWithLayout: IndividualWithPosition[];
  lines: Line[];

  // individuals: Individual[][];
  positionedIndividuals = new Array<IndividualWithPosition[]>();
  private idToPosition: Map<string, IndividualWithPosition> = new Map();

  maximized = false;
  width = 0;
  height = 0;
  scale = 1.0;

  @ViewChild('wrapper')
  private element;

  @Input()
  set family(data: PedigreeData[]) {
    this.family$.next(data);
  }

  private family$ = new BehaviorSubject<PedigreeData[]>(null);
  levels$: Observable<Array<OrderedIndividuals>>;

  private resizeElement: any = null;

  constructor(
    private perfectlyDrawablePedigreeService: PerfectlyDrawablePedigreeService,
    private resizeService: ResizeService,
    private changeDetectorRef: ChangeDetectorRef
  ) { }

  private maximizeSubscription: Subscription;

  ngOnInit() {
    this.maximizeSubscription = PedigreeChartComponent.miximizedChart
      .subscribe(chart => {
        if (chart !== this && this.maximized) {
          this.maximized = false;
          this.changeDetectorRef.markForCheck();
        }
      });
    this.pedigreeDataWithLayout = [];
    this.lines = [];

    const familyData = this.family$
      .filter(f => !!f);

    const sandwichResults$ = familyData
      .switchMap(family => {
        if (family.map(member => member.position).some(p => !!p)) {
          this.positionedIndividuals = this.loadPositions(family);
          return Observable.of<void>(null);
        }

        return Observable
          .of(this.perfectlyDrawablePedigreeService.isPDP(family))
          .map(([, intervals]) => intervals)
          .filter(i => !!i)
          .map(i => this.onlyInidividuals(i))
          .map(i => this.getIndividualsByRank(i))
          .map(individuals => {
            for (let i = 0; i < individuals.length; i++) {
              this.positionedIndividuals.push(
                this.generateLayout(individuals[i], i));
            }
            const start = Date.now();
            this.optimizeDrawing(this.positionedIndividuals);

            console.warn('drawing optimizing', Date.now() - start, 'ms');
          });
      });

    sandwichResults$
      .take(1)
      .subscribe(_ => {
        for (const individual of this.positionedIndividuals) {
          this.lines = this.lines.concat(
            this.generateLines(individual));
        }

        this.pedigreeDataWithLayout = this.positionedIndividuals
          .reduce((acc, individuals) => acc.concat(individuals), []);

        this.width = this.pedigreeDataWithLayout
          .map(i => i.xUpperLeftCorner + i.size + 1)
          .reduce((acc, current) => Math.max(acc, current), 0);

        this.height = this.pedigreeDataWithLayout
          .map(i => i.yUpperLeftCorner + i.size + 1)
          .reduce((acc, current) => Math.max(acc, current), 0);

        });
  }

  ngOnDestroy() {
    if (this.maximizeSubscription) {
      this.maximizeSubscription.unsubscribe();
      this.maximizeSubscription = null;
    }

    if (this.resizeElement) {
      this.resizeService.removeResizeEventListener(this.resizeElement);
      this.resizeElement = null;
    }
  }

  ngAfterViewInit() {
    this.resizeElement = this.element.nativeElement;
    // console.log(this.element);
    this.resizeService.addResizeEventListener(this.resizeElement, (elem) => {
        this.scaleSvg();
    });
    setTimeout(() => {
        this.scaleSvg();

    });
  }

  get straightLines() {
    return this.lines.filter(line => !line.curved);
  }

  get curveLines() {
    return this.lines.filter(line => line.curved);
  }

  scaleSvg() {
    if (!this.element) {
      return;
    }
    const box = this.element.nativeElement.getBoundingClientRect();
    if (!box) {
      return;
    }
    const height = box.height;
    const width = box.width;

    if (this.maximized) {
      this.scale = 1.0;
    } else if (this.width && this.height) {
      this.scale = Math.min(1.0, width / this.width, height / this.height);
    } else {
      return;
    }

    this.changeDetectorRef.markForCheck();
  }

  toggleMaximize() {
    if (!this.maximized) {
      this.maximized = true;
      PedigreeChartComponent.miximizedChart.next(this);
    } else {
      this.maximized = false;
    }
  }

  getScaleString() {
    return `scale(${this.scale})`;
  }

  getViewBox() {
    const sortedCurveLines = this.curveLines.sort(curveLine => curveLine.inverseCurveP1[1]);

    if (sortedCurveLines.length !== 0) {
      const minY = sortedCurveLines[0].inverseCurveP1[1];
      if (minY < 0) {
        return '-8 ' + minY.toString() + ' ' + (this.width + 8.0).toString() + ' ' + (this.height + (-minY) + 8.0).toString();
      }
    }

    return '-8 0 ' + (this.width + 8.0) + ' ' + (this.height + 8.0);
  }

  private loadPositions(family: PedigreeData[]) {
    const individualsWithPosition = this.perfectlyDrawablePedigreeService
      .getIndividuals(family)
      .map(person => new IndividualWithPosition(person,
          person.pedigreeData.position[0], person.pedigreeData.position[1], 21, 1.0));

    let minY = Math.min(...individualsWithPosition
      .map(p => p.yUpperLeftCorner));
    minY -= 1;

    let minX = Math.min(...individualsWithPosition
      .map(p => p.xUpperLeftCorner));
    minX -= 1;

    for (const individual of individualsWithPosition) {
      this.idToPosition.set(individual.individual.pedigreeData.id, individual);
      individual.xCenter -= minX;
      individual.yCenter -= minY;
    }

    const individuals = individualsWithPosition
      .reduce((acc, person) => {
        this.idToPosition.set(person.individual.pedigreeData.id, person);

        const row = acc.find(arr => arr[0].yCenter === person.yCenter);

        if (row) {
          row.push(person);
        } else {
          acc.push([person]);
        }
        return acc;
      }, [] as IndividualWithPosition[][])
      .sort((arr1, arr2) => arr1[0].yCenter - arr2[0].yCenter);

      // for (let line of individuals) {
      //   line = line.sort((i1, i2) => i1.xCenter '(window:resize)': 'onResize($event)'- i2.xCenter);
      // }

    return individuals
      .map(line => line.sort((i1, i2) => i1.xCenter - i2.xCenter));
  }

  getIndividualsByRank(individuals: IntervalForVertex<Individual>[]) {
    const individualsByRank = individuals.reduce((acc, individual) => {
      if (acc.has(individual.vertex.rank)) {
        acc.get(individual.vertex.rank).push(individual);
      } else {
        acc.set(individual.vertex.rank, [individual]);
      }
      return acc;
    }, new Map<number, IntervalForVertex<Individual>[]>());

    const keys: Array<number> = [];
    const rankIterator = individualsByRank.keys();
    let itResult = rankIterator.next();
    while (!itResult.done) {
      keys.push(itResult.value);
      itResult = rankIterator.next();
    }

    const result: OrderedIndividuals[] = [];
    for (const key of keys.sort()) {
        const sorted = individualsByRank.get(key)
          .sort((a, b) => a.left - b.left);

        // console.log(sorted.map(i => i.toString()));
        result.push(sorted.map(interval => interval.vertex));
    }

    return result;
  }

  onlyInidividuals(intervals: IntervalForVertex<IndividualSet>[]) {
    return intervals
        .filter(interval => interval.vertex instanceof Individual)
        .map(i => i as IntervalForVertex<Individual>);
  }

  private alignParentsOfChildren(individuals: IndividualWithPosition[][]) {
    let result = 0;
    for (let i = individuals.length - 1; i > 0; i--) {
      const sibships = this.getSibsipsOnLevel(individuals[i]);
      for (const group of sibships) {
        result += this.centerParentsOfChildren(group);
      }
    }

    return result;
  }


  private alignChildrenOfParents(individuals: IndividualWithPosition[][]) {
    let result = 0;
    for (let i = 0; i < individuals.length - 1; i++) {
      const matingUnits = this.getMatingUnitsOnLevel(individuals[i]);

      for (const mates of matingUnits) {
        result += this.centerChildrenOfParents(mates);
      }
    }

    return result;
  }

  private optimizeDrawing(individuals: IndividualWithPosition[][], xOffset = 20) {
    let movedIndividuals = 0;
    let counter = 0;
    do {
      counter++;
      movedIndividuals = 0;
      if (counter % 6 < 3) {
        movedIndividuals += this.alignParentsOfChildren(individuals);
        movedIndividuals += this.alignChildrenOfParents(individuals);
      } else {
        movedIndividuals += this.alignChildrenOfParents(individuals);
        movedIndividuals += this.alignParentsOfChildren(individuals);
      }

      movedIndividuals += this.moveOverlaps(individuals);
      // console.log('After removing overlaps:', movedIndividuals);
    } while (movedIndividuals !== 0 && counter < 100);
    // console.log('Done', movedIndividuals, counter);

    this.alignLeft(individuals, xOffset);
  }

  private setMatesEquallyApart(levels: IndividualWithPosition[][]) {
    let movedIndividuals = 0;
    for (const level of levels) {
      const matingUnits = level
        .filter(i => i.individual.matingUnits)
        .filter(i => i.individual.matingUnits.length === 2)
        .map(i => [i.individual.matingUnits[0], i.individual.matingUnits[1]] as [MatingUnit, MatingUnit]);

      for (const [m1, m2] of matingUnits) {
        const sameFather = (m1.father === m2.father);
        const orderedMates: Individual[] = [];

        if (sameFather) {
          orderedMates.push(m1.mother);
          orderedMates.push(m1.father);
          orderedMates.push(m2.mother);
        } else {
          orderedMates.push(m1.father);
          orderedMates.push(m1.mother);
          orderedMates.push(m2.father);
        }
        const mateCoordinates = orderedMates.map(i => this.idToPosition.get(i.pedigreeData.id));
        if (mateCoordinates[0].xCenter > mateCoordinates[2].xCenter) {
          const temp = mateCoordinates[0];
          mateCoordinates[0] = mateCoordinates[2];
          mateCoordinates[2] = temp;
        }

        // console.log(m1, m2);
        const dist1 = mateCoordinates[1].xCenter - mateCoordinates[0].xCenter;
        const dist2 = mateCoordinates[2].xCenter - mateCoordinates[1].xCenter;

        if (dist1 < 0 || dist2 < 0) {
            console.warn('negative dist...', dist1, dist2);
            return 0;
        }
        if (Math.abs(dist1 - dist2) < 1e-7) {
            // console.log('negative dist...', dist1, dist2);
          return 0;
        }

        if (dist1 > dist2) {
          movedIndividuals += this.move(mateCoordinates.slice(2, 3), dist1 - dist2);
        } else {
          movedIndividuals += this.move(mateCoordinates.slice(1, 3), dist2 - dist1);
        }
      }
    }
    return movedIndividuals;
  }

  private moveOverlaps(levels: IndividualWithPosition[][]) {
    let movedIndividuals = 0;
    const minGap = levels[0][0].size + 8;
    for (const level of levels) {
      for (let i = 0; i < level.length - 1; i++) {
        const j = i + 1;
        if (j >= level.length) {
          continue;
        }
        const diff = level[j].xCenter - level[i].xCenter;
        if (diff < 0) {
            console.warn('Some reordering has happened!', diff, level[i], level[j]);
        }
        if (minGap - diff > 1) {
          const individualsToMove = [level[j]];
          movedIndividuals += this.move(individualsToMove, minGap - diff);
        }
      }
    }
    return movedIndividuals;
  }

  private getMatingUnitsOnLevel(level: IndividualWithPosition[]) {
    const matingUnits = level
      .filter(member => !!member.individual.matingUnits.length)
      .map(member => member.individual.matingUnits)
      .reduce((acc, mu) => acc.concat(mu), []);

    return Array.from(new Set(matingUnits));
  }

  private getSibsipsOnLevel(level: IndividualWithPosition[]) {
    const result: IndividualWithPosition[][] = [];
    let matingUnits = level
      .filter(member => !!member.individual.parents)
      .map(member => member.individual.parents.father.matingUnits)
      .reduce((acc, mu) => acc.concat(mu), []);

    matingUnits = Array.from(new Set(matingUnits));

    for (const mates of matingUnits) {
      const [first, last] = this.getFirstAndLastChild(level, mates);
      result.push(level.slice(level.indexOf(first), level.indexOf(last) + 1));
    }
    // return pedigreeDataWithPositions;

    return result;
  }

  private alignLeft(groups: IndividualWithPosition[][], xOffset) {
    const minStartXReducer = (g1, g2) => g1.xCenter < g2.xCenter ? g1 : g2;

    const leftmostGroupX = groups
      .map(group => group.reduce(minStartXReducer).xCenter)
      .reduce((a, b) => Math.min(a, b));

    const toMove = leftmostGroupX - xOffset;
    groups.forEach(g => g.forEach(group => group.xCenter -= toMove));
  }

  private centerChildrenOfParents(mates: MatingUnit) {
    const someChild = this.idToPosition
      .get(mates.children.individuals[0].pedigreeData.id);

    const level = this.getIndividualsOnLevel(someChild);

    const father = this.idToPosition.get(mates.father.pedigreeData.id);
    const mother = this.idToPosition.get(mates.mother.pedigreeData.id);

    const [firstChild, lastChild] = this.getFirstAndLastChild(level, mates);

    if (lastChild == null || firstChild == null) {
      return 0;
    }
    const childrenCenter = (lastChild.xCenter + firstChild.xCenter) / 2;
    const parentsCenter = (father.xCenter + mother.xCenter) / 2;
    const offset = parentsCenter - childrenCenter;


    const children = level.slice(
      level.indexOf(firstChild), level.indexOf(lastChild) + 1);

    if (Math.abs(offset) > 1e-7) {
      return this.move(children, offset) + children.length;
    }
    return 0;
  }

  private getFirstAndLastChild(children: IndividualWithPosition[],
    matingUnit: MatingUnit) {
    return children
      .reduce((acc, m) => {
        if (m.individual.isChildOf(matingUnit.father, matingUnit.mother)) {
          if (!acc[0]) {
            acc[0] = m;
          }
          acc[1] = m;
        }
        return acc;
      }, [null, null] as [IndividualWithPosition, IndividualWithPosition] );
  }

  private centerParentsOfChildren(children: IndividualWithPosition[]) {
    const startX = children[0].xCenter;
    const endX = children[children.length - 1].xCenter;
    const childrenCenter = (endX + startX) / 2;

    const mother = this.idToPosition
      .get(children[0].individual.parents.mother.pedigreeData.id);
    const father = this.idToPosition
      .get(children[0].individual.parents.father.pedigreeData.id);

    const parentsCenter = (father.xCenter + mother.xCenter) / 2;

    const offset = childrenCenter - parentsCenter;


    if (offset !== 0) {
      return this.move([father, mother], offset);
    }
    return 0;
  }

  private assertConsequtive(level: IndividualWithPosition[],
      individuals: IndividualWithPosition[]) {
    const indices = individuals.map(i => level.indexOf(i));
    const firstIndex = indices.reduce((a, b) => Math.min(a, b));
    const lastIndex = indices.reduce((a, b) => Math.max(a, b));

    if (lastIndex - firstIndex + 1 !== individuals.length) {
      console.log('trying to move non-consequtive individuals...', individuals,
        level);
      // debugger;
    }
  }

  private move(individuals: IndividualWithPosition[], offset: number,
      count = 0, alreadyMoved: IndividualWithPosition[]  = []) {
    const level = this.getIndividualsOnLevel(individuals[0]);
    // console.log('moving', individuals, offset);

    if (count > 100) {
      console.log('Too much moving...');
      return 0;
    }
    if (Math.abs(offset) < 1e-5) {
        return 0;
    }

    individuals = Array.from(difference(new Set(individuals), new Set(alreadyMoved)));

    let minIndividual = individuals.reduce((a, b) => a.xCenter < b.xCenter ? a : b);
    let maxIndividual = individuals.reduce((a, b) => a.xCenter > b.xCenter ? a : b);

    if (maxIndividual < minIndividual) {
      console.log('switching min and max...');
      [minIndividual, maxIndividual] = [maxIndividual, minIndividual];
    }

    individuals = level.slice(level.indexOf(minIndividual), level.indexOf(maxIndividual) + 1);
    individuals = Array.from(difference(new Set(individuals), new Set(alreadyMoved)));

    if (individuals.length === 0) {
      return 0;
    }
    this.assertConsequtive(level, individuals);

    let toCheckCollision: IndividualWithPosition[] = [];
    let collisionMove = 0;


    if (offset > 0) {
      const start = minIndividual.xCenter;
      const end = maxIndividual.xCenter;
      const newEnd = end + offset;

      toCheckCollision = this.getIndividualsInRange(level, start, newEnd);
      toCheckCollision = Array.from(
        difference(
          difference(new Set(toCheckCollision), new Set(individuals)),
          new Set(alreadyMoved))
      );
      // console.log('found', toCheckCollision);
      if (toCheckCollision.length) {
        // collisionMove = offset;
        collisionMove = toCheckCollision.map(i => newEnd - i.xCenter + 8 * 2 + i.size)
          .reduce((a, b) => Math.max(a, b));
      }
    } else {
      const start = minIndividual.xCenter;
      const end = maxIndividual.xCenter;
      const newStart = start + offset;

      toCheckCollision = this.getIndividualsInRange(level, newStart, end);
      toCheckCollision = Array.from(
        difference(
          difference(new Set(toCheckCollision), new Set(individuals)),
          new Set(alreadyMoved))
      );
      // console.log('found', toCheckCollision);
      if (toCheckCollision.length) {
        // collisionMove = offset;
        collisionMove = toCheckCollision.map(i => newStart - i.xCenter - 8 * 2 - i.size)
          .reduce((a, b) => Math.min(a, b));
      }
    }

    for (const individual of individuals) {
      individual.xCenter += offset;
    }

    let othersMoved = 0;

    if (toCheckCollision.length) {
      othersMoved = this.move(toCheckCollision, collisionMove, count + 1, alreadyMoved.concat(individuals));
    }

    return individuals.length + othersMoved;
  }

  private getIndividualsInRange(individuals: IndividualWithPosition[], start, end) {
    // console.log('Range:', start, end);
    return individuals.filter(i => i.xCenter >= start && i.xCenter <= end);
  }

  private getIndividualsOnLevel(individual: IndividualWithPosition) {
    for (const level of this.positionedIndividuals) {
      for (const current of level) {
        if (current === individual) {
          return level;
        }
      }
    }
    return null;
  }

  private generateLayout(individuals: Individual[], level: number,
    memberSize = 21, maxGap = 8, totalHeight = 30, xOffset = 20) {
    const result: IndividualWithPosition[] = [];
    const initialxOffset = xOffset;


    for (const individual of individuals) {
      const position = new IndividualWithPosition(
        individual, xOffset, level * totalHeight + 20, memberSize, 1.0);
      result.push(position);
      this.idToPosition.set(individual.pedigreeData.id, position);
      xOffset += memberSize + maxGap ;
    }

    return result;
  }


  private generateLines(individuals: IndividualWithPosition[], horizontalYOffset = 15) {
    const lines = new Array<Line>();
    const connections = new Array<Set<Individual>>();

    const lineY = individuals[0].yCenter - horizontalYOffset;

    for (let i = 0; i < individuals.length; i++) {
      const current = individuals[i];
      if (current.individual.parents) {
        lines.push(new Line(current.xCenter, current.yCenter, current.xCenter, lineY));
      }
      if (i + 1 < individuals.length) {
        for (let j = i + 1; j < individuals.length; j++) {
          const other = individuals[j];
          const areNextToEachother = ((i + 1) === j);

          if (current.individual.areMates(other.individual) &&
              !connections.includes(new Set([current.individual, other.individual]))) {
            const middleX = (current.xCenter + other.xCenter) / 2;
            if (areNextToEachother) {
              lines.push(new Line(current.xCenter, current.yCenter,
                other.xCenter, other.yCenter));
              lines.push(new Line(middleX, current.yCenter, middleX, individuals[0].yCenter + horizontalYOffset));
            } else {
              const line = new Line(current.xCenter, current.yCenter,
                other.xCenter, other.yCenter, true, horizontalYOffset);

                const percentX = (middleX - current.xCenter) / (other.xCenter - current.xCenter);
                const centerY = line.inverseCurveYAt(percentX);

              lines.push(line);
              lines.push(new Line(middleX, centerY, middleX, individuals[0].yCenter + horizontalYOffset));
            }
            connections.push(new Set([current.individual, other.individual]));
          }
        }
      }
    }

    for (let i = 0; i < individuals.length; i++) {
      const current = individuals[i];
      if (!current.individual.parents) {
        continue;
      }
      for (let j = individuals.length - 1; j > i; j--) {
        const other = individuals[j];
        if (current.individual.areSiblings(other.individual)) {
          lines.push(new Line(current.xCenter, lineY, other.xCenter, lineY));
          i = j;
          break;
        }
      }
    }


    // }


    return lines;
  }


}
