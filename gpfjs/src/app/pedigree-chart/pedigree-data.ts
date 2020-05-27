import { PedigreeData } from '../genotype-preview-model/genotype-preview';
import { IntervalForVertex } from '../utils/interval-sandwich';

export abstract class IndividualSet {

    abstract individualSet(): Set<Individual>;

    generationRanks(): Set<number> {
      const individuals = this.individualSet();
      const ranks = new Set();

      individuals.forEach(individual => ranks.add(individual.rank));

      return ranks;
    }

    abstract childrenSet(): Set<Individual>;

}

export class ParentalUnit {
  constructor(
    public mother: Individual,
    public father: Individual
  ) {}
}

export const NO_RANK = -3673473456;

export class Individual extends IndividualSet {
  matingUnits = new Array<MatingUnit>();
  pedigreeData: PedigreeData;
  parents: ParentalUnit;
  rank: number = NO_RANK;

  individualSet() {
    return new Set([this]);
  }

  toString() {
    try {
      return this.pedigreeData.id;
    } catch (exception) {
      console.error(exception);
    }
  }

  addRank(rank: number) {
    if (this.rank !== NO_RANK) {
      return;
    }

    this.rank = rank;

    for (const matingUnit of this.matingUnits) {
      matingUnit.children.individuals.forEach(child => {
        child.addRank(rank - 1);
      });

      matingUnit.father.addRank(rank);
      matingUnit.mother.addRank(rank);

    }
    if (this.parents) {
      if (this.parents.father) { this.parents.father.addRank(rank + 1); }
      if (this.parents.mother) { this.parents.mother.addRank(rank + 1); }
    }
  }

  childrenSet() {
    const childrenSet = new Set<Individual>();

    for (const matingUnit of this.matingUnits) {
      matingUnit.childrenSet().forEach(child => childrenSet.add(child));
    }

    return childrenSet;
  }


  areMates(second: Individual) {
    let areInMatingUnit = false;

    for (const matingUnit of this.matingUnits) {
      if (matingUnit.father === second || matingUnit.mother === second) {
        areInMatingUnit = true;
      }
    }

    return areInMatingUnit;
  }

  areSiblings(second: Individual) {
    if (!this.parents || !second.parents) {
      return false;
    }

    if (this.parents.father === second.parents.father &&
        this.parents.mother === second.parents.mother) {
        return true;
      }

    return false;
  }

  isChildOf(father: Individual, mother?: Individual) {
    if (!this.parents) {
      return false;
    }
    if (mother) {
      return this.parents.father === father && this.parents.mother === mother;
    }
    return this.parents.father === father;
  }
}

export class MatingUnit extends IndividualSet {
  children = new SibshipUnit();
  visited = false;

  constructor(
    readonly mother: Individual,
    readonly father: Individual
  ) {
    super();
    mother.matingUnits.push(this);
    father.matingUnits.push(this);
  }

  toString() {
    const ids = this.individualSet();
    const sortedIds = Array.from(ids)
      .map(individual => individual.pedigreeData.id)
      .sort((a, b) => a.localeCompare(b))
      .join(',');
    return `m{${sortedIds}}`;
  }

  individualSet() {
    return new Set([this.mother, this.father]);
  }

  childrenSet() {
    return new Set(this.children.individuals);
  }
}

export class MatingUnitWithIntervals {
  constructor(
    public mother: IntervalForVertex<Individual>,
    public father: IntervalForVertex<Individual>,
    public children: Array<IntervalForVertex<Individual>>,
  ) {}
}

export class SibshipUnit extends IndividualSet {
  individuals = new Array<Individual>();

  toString() {
    const ids = this.individualSet();
    const sortedIds = Array.from(ids)
      .map(individual => individual.pedigreeData.id)
      .sort((a, b) => a.localeCompare(b))
      .join(',');
    return `s{${sortedIds}}`;
  }

  individualSet() {
    return new Set(this.individuals);
  }

  childrenSet() {
    return new Set();
  }
}


export class IndividualWithPosition  {
  constructor(
    public individual: Individual,
    public xCenter: number,
    public yCenter: number,
    public size: number,
    public scaleFactor: number
  ) { }

  get xUpperLeftCorner() {
    return this.xCenter - this.size / 2;
  }

  get yUpperLeftCorner() {
    return this.yCenter - this.size / 2;
  }
}

export class Line {
  constructor(
    public startX: number,
    public startY: number,
    public endX: number,
    public endY: number,
    public curved: boolean = false,
    public curvedBaseHeight: number = NaN
  ) { }

  get path() {
    return 'M' + this.curveP0[0].toString() + ',' + this.curveP0[1].toString() +
      ' C' + this.curveP1[0].toString() + ',' + this.inverseCurveP1[1].toString() + ' ' +
      this.curveP2[0].toString() + ',' + this.curveP2[1].toString() + ' ' +
      this.curveP3[0].toString() + ',' + this.curveP3[1].toString();
  }

  get curveP0() {
    return [this.startX, this.startY];
  }

  get curveP1() {
    return [this.startX + 10, this.startY + this.curvedBaseHeight * 3.0];
  }

  get curveP2() {
    return [this.endX, this.endY];
  }

  get curveP3() {
    return [this.endX, this.endY];
  }

  get inverseCurveP1() {
    return [this.startX + 10, this.startY - this.curvedBaseHeight * 3.0];
  }

  get inverseCurveP2() {
    return [this.endX, this.endY];
  }

  curveYAt(t: number) {
    const one_minus_t = 1.0 - t;

    return (one_minus_t ** 3) * this.curveP0[1] +
        3 * (one_minus_t ** 2) * t * this.curveP1[1] +
        3 * one_minus_t * (t ** 2) * this.curveP2[1] +
        (t ** 3) * this.curveP3[1];
  }

  inverseCurveYAt(t: number) {
    const one_minus_t = 1.0 - t;

    return (one_minus_t ** 3) * this.curveP0[1] +
        3 * (one_minus_t ** 2) * t * this.inverseCurveP1[1] +
        3 * one_minus_t * (t ** 2) * this.inverseCurveP2[1] +
        (t ** 3) * this.curveP3[1];
  }
}

export class SameLevelGroup {
  constructor(
    public yCenter: number,
    public members: Individual[] = [],
    public startX = 0,
    public memberSize = 21,
    public gapSize = 8
  ) {}

  get width() {
    return Math.max(0, this.members.length * this.memberSize +
      (this.members.length - 1) * this.gapSize);
  }

  get lastMember() {
    if (this.members.length === 0) {
      return null;
    }
    return this.members[this.members.length - 1];
  }

  get individualsWithPositions() {
    const result: Array<IndividualWithPosition> = [];

    for (let i = 0; i < this.members.length; i++) {
      result.push(new IndividualWithPosition(
        this.members[i], this.getXFromIndex(i), this.yCenter,
        this.memberSize, 1.0)
      );
    }

    return result;
  }

  private getXFromIndex(i: number) {
    return this.startX + i * this.memberSize +
      i * this.gapSize;
  }

  getXForMember(member: Individual) {
    const index = this.members.indexOf(member);
    if (index === -1) {
      return -1;
    }
    return this.getXFromIndex(index);
  }

}
