import { Input, Component, OnInit, ChangeDetectionStrategy } from '@angular/core';

import { PedigreeData } from '../genotype-preview-model/genotype-preview';
import { Individual, IndividualWithPosition, Line, MatingUnit, ParentalUnit } from './pedigree-data';
import { difference } from '../utils/sets-helper';

@Component({
  selector: '[gpf-pedigree-chart-level]',
  templateUrl: './pedigree-chart-level.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class PedigreeChartLevelComponent implements OnInit {
  pedigreeDataWithLayout: IndividualWithPosition[];
  lines: Line[];
  blownFuse = false;

  @Input() connectingLineYPosition: number;
  @Input() individuals: Individual[][];
  positionedIndividuals = new Array<IndividualWithPosition[]>();
  // groups: SameLevelGroup[][] = new Array<SameLevelGroup[]>();
  private idToPosition: Map<string, IndividualWithPosition> = new Map();

  ngOnInit() {
    this.pedigreeDataWithLayout = [];
    this.lines = [];

    if (this.individuals) {
      for (let i = 0; i < this.individuals.length; i++) {
        this.positionedIndividuals.push(
          this.generateLayout(this.individuals[i], i));
      }
      let start = Date.now();
      this.optimizeDrawing(this.positionedIndividuals);
      console.warn("drawing optimizing", Date.now() - start, "ms");
      for (let individual of this.positionedIndividuals) {
        this.lines = this.lines.concat(
          this.generateLines(individual));
      }

    }

    this.pedigreeDataWithLayout = this.positionedIndividuals
      .reduce((acc, individuals) => acc.concat(individuals), []);

  }

  private alignParentsOfChildren(individuals: IndividualWithPosition[][]) {
    let result = 0;
    for (let i = individuals.length - 1; i > 0; i--) {
      let sibships = this.getSibsipsOnLevel(individuals[i]);
      for (let group of sibships) {
        result += this.centerParentsOfChildren(group);
      }
    }

    return result;
  }


  private alignChildrenOfParents(individuals: IndividualWithPosition[][]) {
    let result = 0;
    for (let i = 0; i < individuals.length - 1; i++) {
      let matingUnits = this.getMatingUnitsOnLevel(individuals[i]);

      for (let mates of matingUnits) {
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

      // console.log("After aligning parents:", movedIndividuals);


      // console.log("After aligning children:", movedIndividuals);
    //   movedIndividuals += this.setMatesEquallyApart(individuals);
      // console.log("After setting equal mate lengths:", movedIndividuals);
      movedIndividuals += this.moveOverlaps(individuals);
      // console.log("After removing overlaps:", movedIndividuals);
    } while (movedIndividuals !== 0 && counter < 100);
    // console.log("Done", movedIndividuals, counter);

    this.alignLeft(individuals, xOffset);
  }

  private setMatesEquallyApart(levels: IndividualWithPosition[][]) {
    let movedIndividuals = 0;
    for (let level of levels) {
      let matingUnits = level
        .filter(i => i.individual.matingUnits)
        .filter(i => i.individual.matingUnits.length === 2)
        .map(i => [i.individual.matingUnits[0], i.individual.matingUnits[1]] as [MatingUnit, MatingUnit]);

      for (let [m1, m2] of matingUnits) {
        let sameFather = (m1.father === m2.father);
        let orderedMates: Individual[] = [];

        if (sameFather) {
          orderedMates.push(m1.mother);
          orderedMates.push(m1.father);
          orderedMates.push(m2.mother);
        } else {
          orderedMates.push(m1.father);
          orderedMates.push(m1.mother);
          orderedMates.push(m2.father);
        }
        let mateCoordinates = orderedMates.map(i => this.idToPosition.get(i.pedigreeData.id));
        if (mateCoordinates[0].xCenter > mateCoordinates[2].xCenter) {
          let temp = mateCoordinates[0];
          mateCoordinates[0] = mateCoordinates[2];
          mateCoordinates[2] = temp;
        }

        // console.log(m1, m2);
        let dist1 = mateCoordinates[1].xCenter - mateCoordinates[0].xCenter;
        let dist2 = mateCoordinates[2].xCenter - mateCoordinates[1].xCenter;

        if (dist1 < 0 || dist2 < 0) {
            console.warn('negative dist...', dist1, dist2);
            return 0;
        }
        if (Math.abs(dist1 - dist2) < 1e-7) {
            // console.log("negative dist...", dist1, dist2);
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
    let minGap = levels[0][0].size + 8;
    for (let level of levels) {
      for (let i = 0; i < level.length - 1; i++) {
        let j = i + 1;
        if (j >= level.length) {
          continue;
        }
        let diff = level[j].xCenter - level[i].xCenter;
        if (diff < 0) {
            console.warn('Some reordering has happened!', diff, level[i], level[j]);
        }
        if (minGap - diff > 1) {
          let individualsToMove = [level[j]];
          movedIndividuals += this.move(individualsToMove, minGap - diff);
        }
      }
    }
    return movedIndividuals;
  }

  private getMatingUnitsOnLevel(level: IndividualWithPosition[]) {
    let matingUnits = level
      .filter(member => !!member.individual.matingUnits.length)
      .map(member => member.individual.matingUnits)
      .reduce((acc, mu) => acc.concat(mu), []);

    return Array.from(new Set(matingUnits));
  }

  private getSibsipsOnLevel(level: IndividualWithPosition[]) {
    let result: IndividualWithPosition[][] = [];
    let matingUnits = level
      .filter(member => !!member.individual.parents)
      .map(member => member.individual.parents.father.matingUnits)
      .reduce((acc, mu) => acc.concat(mu), []);

    matingUnits = Array.from(new Set(matingUnits));

    for (let mates of matingUnits) {
      let [first, last] = this.getFirstAndLastChild(level, mates);
      result.push(level.slice(level.indexOf(first), level.indexOf(last) + 1));
    }
    // return pedigreeDataWithPositions;

    return result;
  }

  private alignLeft(groups: IndividualWithPosition[][], xOffset) {
    let minStartXReducer = (g1, g2) => g1.xCenter < g2.xCenter ? g1 : g2;

    let leftmostGroupX = groups
      .map(group => group.reduce(minStartXReducer).xCenter)
      .reduce((a, b) => Math.min(a, b));

    let toMove = leftmostGroupX - xOffset;
    groups.forEach(g => g.forEach(group => group.xCenter -= toMove));
  }

  private centerChildrenOfParents(mates: MatingUnit) {
    let someChild = this.idToPosition
      .get(mates.children.individuals[0].pedigreeData.id);

    let level = this.getIndividualsOnLevel(someChild);

    let father = this.idToPosition.get(mates.father.pedigreeData.id);
    let mother = this.idToPosition.get(mates.mother.pedigreeData.id);

    let [firstChild, lastChild] = this.getFirstAndLastChild(level, mates);

    let childrenCenter = (lastChild.xCenter + firstChild.xCenter) / 2;
    let parentsCenter = (father.xCenter + mother.xCenter) / 2;
    let offset = parentsCenter - childrenCenter;

    // console.log("moving children!");
    // console.log("children center:", childrenCenter);
    // console.log("parents center:", parentsCenter);
    // console.log("offset", offset);

    let children = level.slice(
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
    let startX = children[0].xCenter;
    let endX = children[children.length - 1].xCenter;
    let childrenCenter = (endX + startX) / 2;

    let mother = this.idToPosition
      .get(children[0].individual.parents.mother.pedigreeData.id);
    let father = this.idToPosition
      .get(children[0].individual.parents.father.pedigreeData.id);

    let parentsCenter = (father.xCenter + mother.xCenter) / 2;

    let offset = childrenCenter - parentsCenter;

    // console.log("moving parents!");
    // console.log("children center:", childrenCenter);
    // console.log("parents center:", parentsCenter);
    // console.log("offset", offset);


    if (offset !== 0) {
      return this.move([father, mother], offset);
    }
    return 0;
  }

  private assertConsequtive(level: IndividualWithPosition[],
      individuals: IndividualWithPosition[]) {
    let indices = individuals.map(i => level.indexOf(i));
    let firstIndex = indices.reduce((a, b) => Math.min(a, b));
    let lastIndex = indices.reduce((a, b) => Math.max(a, b));

    if (lastIndex - firstIndex + 1 !== individuals.length) {
      console.log('trying to move non-consequtive individuals...', individuals,
        level);
      // debugger;
    }
  }

  private move(individuals: IndividualWithPosition[], offset: number,
      count = 0, alreadyMoved: IndividualWithPosition[]  = []) {
    let level = this.getIndividualsOnLevel(individuals[0]);
    // console.log("moving", individuals, offset);

    if (count > 100) {
      console.log("Too much moving...");
      return 0;
    }
    if (Math.abs(offset) < 1e-5) {
        return 0;
    }

    individuals = Array.from(difference(new Set(individuals), new Set(alreadyMoved)));

    let minIndividual = individuals.reduce((a, b) => a.xCenter < b.xCenter ? a : b);
    let maxIndividual = individuals.reduce((a, b) => a.xCenter > b.xCenter ? a : b);

    if (maxIndividual < minIndividual) {
      console.log("switching min and max...");
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
      let start = minIndividual.xCenter;
      let end = maxIndividual.xCenter;
      let newEnd = end + offset;

      toCheckCollision = this.getIndividualsInRange(level, start, newEnd);
      toCheckCollision = Array.from(
        difference(
          difference(new Set(toCheckCollision), new Set(individuals)),
          new Set(alreadyMoved))
      );
      // console.log("found", toCheckCollision);
      if (toCheckCollision.length) {
        // collisionMove = offset;
        collisionMove = toCheckCollision.map(i => newEnd - i.xCenter + 8 * 2 + i.size)
          .reduce((a, b) => Math.max(a, b));
      }
    } else {
      let start = minIndividual.xCenter;
      let end = maxIndividual.xCenter;
      let newStart = start + offset;

      toCheckCollision = this.getIndividualsInRange(level, newStart, end);
      toCheckCollision = Array.from(
        difference(
          difference(new Set(toCheckCollision), new Set(individuals)),
          new Set(alreadyMoved))
      );
      // console.log("found", toCheckCollision);
      if (toCheckCollision.length) {
        // collisionMove = offset;
        collisionMove = toCheckCollision.map(i => newStart - i.xCenter - 8 * 2 - i.size)
          .reduce((a, b) => Math.min(a, b));
      }
    }

    for (let individual of individuals) {
      individual.xCenter += offset;
    }

    // console.log("New center:", (individuals.reduce((a, b) => Math.max(a.xCenter, b.xCenter) ? a : b).xCenter
    // + individuals.reduce((a, b) => Math.min(a.xCenter, b.xCenter) ? a : b).xCenter) / 2)

    let othersMoved = 0;

    if (toCheckCollision.length) {
      othersMoved = this.move(toCheckCollision, collisionMove, count + 1, alreadyMoved.concat(individuals));
    }

    return individuals.length + othersMoved;
  }

  private getIndividualsInRange(individuals: IndividualWithPosition[], start, end) {
    // console.log("Range:", start, end);
    return individuals.filter(i => i.xCenter >= start && i.xCenter <= end);
  }

  private getIndividualsOnLevel(individual: IndividualWithPosition) {
    for (let level of this.positionedIndividuals) {
      for (let current of level) {
        if (current === individual) {
          return level;
        }
      }
    }
    return null;
  }

  private generateLayout(individuals: Individual[], level: number,
    memberSize = 21, maxGap = 8, totalHeight = 30, xOffset = 20) {
    let result: IndividualWithPosition[] = [];
    let initialxOffset = xOffset;


    for (let individual of individuals) {
      let position = new IndividualWithPosition(
        individual, xOffset, level * totalHeight + 20, memberSize, 1.0);
      result.push(position);
      this.idToPosition.set(individual.pedigreeData.id, position);
      xOffset += memberSize + maxGap ;
    }

    return result;
  }


  private generateLines(individuals: IndividualWithPosition[], horizontalYOffset = 15) {
    let lines = new Array<Line>();

    // let individuals = group.individualsWithPositions;

    // for (let group of pedigreeData) {
    let lineY = individuals[0].yCenter - horizontalYOffset;

    for (let i = 0; i < individuals.length; i++) {
      let current = individuals[i];
      if (current.individual.parents) {
        lines.push(new Line(current.xCenter, current.yCenter, current.xCenter, lineY));
      }
      if (i + 1 < individuals.length) {
        let other = individuals[i + 1];

        if (current.individual.areMates(other.individual)) {
          let middleX = (current.xCenter + other.xCenter) / 2;
          lines.push(new Line(current.xCenter, current.yCenter,
            other.xCenter, other.yCenter));
          lines.push(new Line(middleX, current.yCenter, middleX, individuals[0].yCenter + horizontalYOffset));
        }
      }
    }

    for (let i = 0; i < individuals.length; i++) {
      let current = individuals[i];
      for (let j = individuals.length - 1; j > i; j--) {
        let other = individuals[j];
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
