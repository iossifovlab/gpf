import { Input, Component, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { Observable, BehaviorSubject, of } from 'rxjs';
import { difference } from '../utils/sets-helper';
import { IntervalForVertex } from '../utils/interval-sandwich';
import { PedigreeData } from '../genotype-preview-model/genotype-preview';
import { PerfectlyDrawablePedigreeService } from '../perfectly-drawable-pedigree/perfectly-drawable-pedigree.service';
import { IndividualWithPosition, Line, IndividualSet, Individual, MatingUnit } from './pedigree-data';
import { filter, map, switchMap, take } from 'rxjs/operators';

type OrderedIndividuals = Array<Individual>;

@Component({
    selector: 'gpf-pedigree-chart',
    templateUrl: './pedigree-chart.component.html',
    styleUrls: ['./pedigree-chart.component.css'],
    changeDetection: ChangeDetectionStrategy.OnPush,
    standalone: false
})
export class PedigreeChartComponent implements OnInit {
  public pedigreeDataWithLayout: IndividualWithPosition[];
  public lines: Line[];

  public positionedIndividuals = new Array<IndividualWithPosition[]>();
  private idToPosition: Map<string, IndividualWithPosition> = new Map();

  public width = 0;
  public height = 0;
  @Input() public scale = 1.3;
  @Input() public maxWidth: number;
  @Input() public maxHeight: number;

  @Input()
  public set family(data: PedigreeData[]) {
    this.family$.next(data);
  }

  @Input() public groupName: string;
  @Input() public counterId: number;

  private family$ = new BehaviorSubject<PedigreeData[]>(null);
  public levels$: Observable<Array<OrderedIndividuals>>;

  public constructor(
    private perfectlyDrawablePedigreeService: PerfectlyDrawablePedigreeService
  ) { }

  public ngOnInit(): void {
    this.pedigreeDataWithLayout = [];
    this.positionedIndividuals = [];
    this.lines = [];

    const familyData = this.family$.pipe(filter(f => Boolean(f)));
    const sandwichResults$ = familyData.pipe(
      switchMap(family => {
        if (family.map(member => member.position).some(p => Boolean(p))) {
          this.positionedIndividuals = this.loadPositions(family);
          return of<void>(null);
        }
        return of(this.perfectlyDrawablePedigreeService.isPDP(family)).pipe(
          map(([, intervals]) => intervals),
          filter(i => Boolean(i)),
          map(i => this.onlyInidividuals(i)),
          map(i => this.getIndividualsByRank(i)),
          map(individuals => {
            for (let i = 0; i < individuals.length; i++) {
              this.positionedIndividuals.push(this.generateLayout(individuals[i], i));
            }
            this.optimizeDrawing(this.positionedIndividuals);
          })
        );
      })
    );

    sandwichResults$.pipe(take(1)).subscribe(() => {
      for (const individual of this.positionedIndividuals) {
        this.lines = this.lines.concat(this.generateLines(individual));
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

  public get straightLines(): Line[] {
    return this.lines.filter(line => !line.curved);
  }

  public get curveLines(): Line[] {
    return this.lines.filter(line => line.curved);
  }

  public getViewBox(): string {
    const scaleDownIndex = 1.3;

    const viewBoxWidth = this.round(this.width * scaleDownIndex);
    let viewBoxHeight = this.round(this.height * scaleDownIndex);
    const viewBoxWidthOffset = this.round((viewBoxWidth - this.width) / 2);
    let viewBoxHeightOffset = this.round((viewBoxHeight - this.height) / 2);

    if (this.curveLines.length !== 0) {
      // if the pedigre has curved lines on top, add extra space on top
      const curveLinesOnTop = this.curveLines
        .map(curveLine => curveLine.startY)
        .filter(curveLineStartY => curveLineStartY <= 12).length !== 0;

      if (curveLinesOnTop) {
        viewBoxHeight += 12;
        viewBoxHeightOffset += 12;
      }
    }

    if (this.pedigreeDataWithLayout.map(a => a.yCenter).every((val, i, arr) => val === arr[0])) {
      // if the pedigree has only a single row, add extra space on bottom for the proband arrow
      viewBoxHeight += 6;
    }

    return `${-viewBoxWidthOffset} ${-viewBoxHeightOffset} ${viewBoxWidth} ${viewBoxHeight}`;
  }

  private round(num: number): number {
    return (Math.round(100 * num) + Number.EPSILON) / 100;
  }

  private loadPositions(family: PedigreeData[]): IndividualWithPosition[][] {
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

    return individuals.map(line => line.sort((i1, i2) => i1.xCenter - i2.xCenter));
  }

  public getIndividualsByRank(individuals: IntervalForVertex<Individual>[]): OrderedIndividuals[] {
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
      const sorted = individualsByRank.get(key).sort((a, b) => a.left - b.left);
      result.push(sorted.map(interval => interval.vertex));
    }

    return result;
  }

  public onlyInidividuals(intervals: IntervalForVertex<IndividualSet>[]): IntervalForVertex<Individual>[] {
    return intervals
      .filter(interval => interval.vertex instanceof Individual)
      .map(i => i as IntervalForVertex<Individual>);
  }

  private alignParentsOfChildren(individuals: IndividualWithPosition[][]): number {
    let result = 0;
    for (let i = individuals.length - 1; i > 0; i--) {
      const sibships = this.getSibsipsOnLevel(individuals[i]);
      for (const group of sibships) {
        result += this.centerParentsOfChildren(group);
      }
    }

    return result;
  }


  private alignChildrenOfParents(individuals: IndividualWithPosition[][]): number {
    let result = 0;
    for (let i = 0; i < individuals.length - 1; i++) {
      const matingUnits = this.getMatingUnitsOnLevel(individuals[i]);

      for (const mates of matingUnits) {
        result += this.centerChildrenOfParents(mates);
      }
    }

    return result;
  }

  private optimizeDrawing(individuals: IndividualWithPosition[][]): void {
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
    } while (movedIndividuals !== 0 && counter < 100);

    this.alignToTopLeft(individuals);
  }

  private moveOverlaps(levels: IndividualWithPosition[][]): number {
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

  private getMatingUnitsOnLevel(level: IndividualWithPosition[]): MatingUnit[] {
    const matingUnits = level
      .filter(member => Boolean(member.individual.matingUnits.length))
      .map(member => member.individual.matingUnits)
      .reduce((acc, mu) => acc.concat(mu), []);

    return Array.from(new Set(matingUnits));
  }

  private getSibsipsOnLevel(level: IndividualWithPosition[]): IndividualWithPosition[][] {
    const result: IndividualWithPosition[][] = [];
    let matingUnits = level
      .filter(member => Boolean(member.individual.parents))
      .map(member => member.individual.parents.father.matingUnits)
      .reduce((acc, mu) => acc.concat(mu), []);

    matingUnits = Array.from(new Set(matingUnits));

    for (const mates of matingUnits) {
      const [first, last] = this.getFirstAndLastChild(level, mates);
      result.push(level.slice(level.indexOf(first), level.indexOf(last) + 1));
    }
    return result;
  }

  private alignToTopLeft(groups: IndividualWithPosition[][]): void {
    const offset = 11;

    const minStartXReducer = (g1, g2) => g1.xCenter < g2.xCenter ? g1 : g2;
    const minStartYReducer = (g1, g2) => g1.yCenter < g2.yCenter ? g1 : g2;

    const leftmostGroupX = groups.map(group => group.reduce(minStartXReducer).xCenter).reduce((a, b) => Math.min(a, b));
    const leftmostGroupY = groups.map(group => group.reduce(minStartYReducer).yCenter).reduce((a, b) => Math.min(a, b));

    const toMoveX = leftmostGroupX - offset;
    const toMoveY = leftmostGroupY - offset;

    groups.forEach(g => g.forEach(group => {group.xCenter -= toMoveX; group.yCenter -= toMoveY}));
  }

  private centerChildrenOfParents(mates: MatingUnit): number {
    const someChild = this.idToPosition
      .get(mates.children.individuals[0].pedigreeData.id);

    const level = this.getIndividualsOnLevel(someChild);

    const father = this.idToPosition.get(mates.father.pedigreeData.id);
    const mother = this.idToPosition.get(mates.mother.pedigreeData.id);

    const [firstChild, lastChild] = this.getFirstAndLastChild(level, mates);

    if (lastChild === null || firstChild === null) {
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

  private getFirstAndLastChild(
    children: IndividualWithPosition[], matingUnit: MatingUnit
  ): [IndividualWithPosition, IndividualWithPosition] {
    return children
      .reduce((acc, m) => {
        if (m.individual.isChildOf(matingUnit.father, matingUnit.mother)) {
          if (!acc[0]) {
            acc[0] = m;
          }
          acc[1] = m;
        }
        return acc;
      }, [null, null] as [IndividualWithPosition, IndividualWithPosition]);
  }

  private centerParentsOfChildren(children: IndividualWithPosition[]): number {
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

  private move(
    individuals: IndividualWithPosition[],
    offset: number,
    count = 0,
    alreadyMoved: IndividualWithPosition[] = []
  ): number {
    const level = this.getIndividualsOnLevel(individuals[0]);

    if (count > 100) {
      return 0;
    }
    if (Math.abs(offset) < 1e-5) {
      return 0;
    }

    individuals = Array.from(difference(new Set(individuals), new Set(alreadyMoved)));

    let minIndividual = individuals.reduce((a, b) => a.xCenter < b.xCenter ? a : b);
    let maxIndividual = individuals.reduce((a, b) => a.xCenter > b.xCenter ? a : b);

    if (maxIndividual < minIndividual) {
      [minIndividual, maxIndividual] = [maxIndividual, minIndividual];
    }

    individuals = level.slice(level.indexOf(minIndividual), level.indexOf(maxIndividual) + 1);
    individuals = Array.from(difference(new Set(individuals), new Set(alreadyMoved)));

    if (individuals.length === 0) {
      return 0;
    }

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
      if (toCheckCollision.length) {
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
      if (toCheckCollision.length) {
        collisionMove = toCheckCollision
          .map(i => newStart - i.xCenter - 8 * 2 - i.size)
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

  private getIndividualsInRange(individuals: IndividualWithPosition[], start, end): IndividualWithPosition[] {
    return individuals.filter(i => i.xCenter >= start && i.xCenter <= end);
  }

  private getIndividualsOnLevel(individual: IndividualWithPosition): IndividualWithPosition[] {
    for (const level of this.positionedIndividuals) {
      for (const current of level) {
        if (current === individual) {
          return level;
        }
      }
    }
    return null;
  }

  private generateLayout(
    individuals: Individual[],
    level: number,
    memberSize = 21,
    maxGap = 8,
    totalHeight = 30,
    xOffset = 20
  ): IndividualWithPosition[] {
    const result: IndividualWithPosition[] = [];

    for (const individual of individuals) {
      const position = new IndividualWithPosition(
        individual, xOffset, level * totalHeight + 20, memberSize, 1.0);
      result.push(position);
      this.idToPosition.set(individual.pedigreeData.id, position);
      xOffset += memberSize + maxGap;
    }

    return result;
  }

  private generateLines(individuals: IndividualWithPosition[], horizontalYOffset = 15): Line[] {
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
          const areNextToEachother = (i + 1) === j;

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

    return lines;
  }
}
