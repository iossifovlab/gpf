import { PedigreeData } from '../genotype-preview-model/genotype-preview';
import { IntervalForVertex } from '../utils/interval-sandwich';

export abstract class IndividualSet {
  public abstract individualSet(): Set<Individual>;

  public generationRanks(): Set<number> {
    const individuals = this.individualSet();
    const ranks = new Set<number>();

    individuals.forEach(individual => ranks.add(individual.rank));

    return ranks;
  }

  public abstract childrenSet(): Set<Individual>;
}

export class ParentalUnit {
  public constructor(
    public mother: Individual,
    public father: Individual
  ) {}
}

export const NO_RANK = -3673473456;

export class Individual extends IndividualSet {
  public matingUnits = new Array<MatingUnit>();
  public pedigreeData: PedigreeData;
  public parents: ParentalUnit;
  public rank: number = NO_RANK;

  public individualSet(): Set<Individual> {
    return new Set([this]);
  }

  public toString(): string {
    try {
      return this.pedigreeData.id;
    } catch (exception) {
      console.error(exception);
    }
  }

  public addRank(rank: number): void {
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
      if (this.parents.father) {
        this.parents.father.addRank(rank + 1);
      }
      if (this.parents.mother) {
        this.parents.mother.addRank(rank + 1);
      }
    }
  }

  public childrenSet(): Set<Individual> {
    const childrenSet = new Set<Individual>();

    for (const matingUnit of this.matingUnits) {
      matingUnit.childrenSet().forEach(child => childrenSet.add(child));
    }

    return childrenSet;
  }


  public areMates(second: Individual): boolean {
    let areInMatingUnit = false;

    for (const matingUnit of this.matingUnits) {
      if (matingUnit.father === second || matingUnit.mother === second) {
        areInMatingUnit = true;
      }
    }

    return areInMatingUnit;
  }

  public areSiblings(second: Individual): boolean {
    if (!this.parents || !second.parents) {
      return false;
    }

    if (this.parents.father === second.parents.father &&
        this.parents.mother === second.parents.mother) {
      return true;
    }

    return false;
  }

  public isChildOf(father: Individual, mother?: Individual): boolean {
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
  public children = new SibshipUnit();
  public visited = false;

  public constructor(
    public readonly mother: Individual,
    public readonly father: Individual
  ) {
    super();
    mother.matingUnits.push(this);
    father.matingUnits.push(this);
  }

  public toString(): string {
    const ids = this.individualSet();
    const sortedIds = Array.from(ids)
      .map(individual => individual.pedigreeData.id)
      .sort((a, b) => a.localeCompare(b))
      .join(',');
    return `m{${sortedIds}}`;
  }

  public individualSet(): Set<Individual> {
    return new Set([this.mother, this.father]);
  }

  public childrenSet(): Set<Individual> {
    return new Set(this.children.individuals);
  }
}

export class MatingUnitWithIntervals {
  public constructor(
    public mother: IntervalForVertex<Individual>,
    public father: IntervalForVertex<Individual>,
    public children: Array<IntervalForVertex<Individual>>,
  ) {}
}

export class SibshipUnit extends IndividualSet {
  public individuals = new Array<Individual>();

  public toString(): string {
    const ids = this.individualSet();
    const sortedIds = Array.from(ids)
      .map(individual => individual.pedigreeData.id)
      .sort((a, b) => a.localeCompare(b))
      .join(',');
    return `s{${sortedIds}}`;
  }

  public individualSet(): Set<Individual> {
    return new Set(this.individuals);
  }

  public childrenSet(): Set<Individual> {
    return new Set<Individual>();
  }
}


export class IndividualWithPosition {
  public constructor(
    public individual: Individual,
    public xCenter: number,
    public yCenter: number,
    public size: number,
    public scaleFactor: number
  ) { }

  public get xUpperLeftCorner(): number {
    return this.xCenter - this.size / 2;
  }

  public get yUpperLeftCorner(): number {
    return this.yCenter - this.size / 2;
  }
}

export class Line {
  public constructor(
    public startX: number,
    public startY: number,
    public endX: number,
    public endY: number,
    public curved: boolean = false,
    public curvedBaseHeight: number = NaN
  ) { }

  public get path(): string {
    return 'M' + this.curveP0[0].toString() + ',' + this.curveP0[1].toString() +
      ' C' + this.curveP1[0].toString() + ',' + this.inverseCurveP1[1].toString() + ' ' +
      this.curveP2[0].toString() + ',' + this.curveP2[1].toString() + ' ' +
      this.curveP3[0].toString() + ',' + this.curveP3[1].toString();
  }

  public get curveP0(): number[] {
    return [this.startX, this.startY];
  }

  public get curveP1(): number[] {
    return [this.startX + 10, this.startY + this.curvedBaseHeight * 3.0];
  }

  public get curveP2(): number[] {
    return [this.endX, this.endY];
  }

  public get curveP3(): number[] {
    return [this.endX, this.endY];
  }

  public get inverseCurveP1(): number[] {
    return [this.startX + 10, this.startY - this.curvedBaseHeight * 3.0];
  }

  public get inverseCurveP2(): number[] {
    return [this.endX, this.endY];
  }

  public curveYAt(t: number): number {
    const one_minus_t = 1.0 - t;

    return (one_minus_t ** 3) * this.curveP0[1] +
        3 * (one_minus_t ** 2) * t * this.curveP1[1] +
        3 * one_minus_t * (t ** 2) * this.curveP2[1] +
        (t ** 3) * this.curveP3[1];
  }

  public inverseCurveYAt(t: number): number {
    const one_minus_t = 1.0 - t;

    return (one_minus_t ** 3) * this.curveP0[1] +
        3 * (one_minus_t ** 2) * t * this.inverseCurveP1[1] +
        3 * one_minus_t * (t ** 2) * this.inverseCurveP2[1] +
        (t ** 3) * this.curveP3[1];
  }
}

export class SameLevelGroup {
  public constructor(
    public yCenter: number,
    public members: Individual[] = [],
    public startX = 0,
    public memberSize = 21,
    public gapSize = 8
  ) {}

  public get width(): number {
    return Math.max(0, this.members.length * this.memberSize +
      (this.members.length - 1) * this.gapSize);
  }

  public get lastMember(): Individual {
    if (this.members.length === 0) {
      return null;
    }
    return this.members[this.members.length - 1];
  }

  public get individualsWithPositions(): IndividualWithPosition[] {
    const result: Array<IndividualWithPosition> = [];

    for (let i = 0; i < this.members.length; i++) {
      result.push(new IndividualWithPosition(
        this.members[i], this.getXFromIndex(i), this.yCenter,
        this.memberSize, 1.0)
      );
    }

    return result;
  }

  private getXFromIndex(i: number): number {
    return this.startX + i * this.memberSize + i * this.gapSize;
  }

  public getXForMember(member: Individual): number {
    const index = this.members.indexOf(member);
    if (index === -1) {
      return -1;
    }
    return this.getXFromIndex(index);
  }
}
