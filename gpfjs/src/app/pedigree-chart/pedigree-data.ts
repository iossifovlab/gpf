import { PedigreeData } from '../genotype-preview-table/genotype-preview';

export abstract class IndividualSet {

    abstract individualSet(): Set<Individual>;

    generationRanks(): Set<number> {
      let individuals = this.individualSet();
      let ranks = new Set();

      individuals.forEach(individual => ranks.add(individual.rank));

      return ranks;
    }

    abstract childrenSet(): Set<Individual>;

    toString(): string {
      let ids = this.individualSet();
      let sortedIds = Array.from(ids)
        .map(individual => individual.pedigreeData.id)
        .sort((a, b) => a.localeCompare(b));

      return sortedIds.join(',');
    }
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

  addRank(rank: number) {
    if (this.rank !== NO_RANK) {
      return;
    }

    this.rank = rank;

    for (let matingUnit of this.matingUnits) {
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
    let childrenSet = new Set<Individual>();

    for (let matingUnit of this.matingUnits) {
      matingUnit.childrenSet().forEach(child => childrenSet.add(child));
    }

    return childrenSet;
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

  individualSet() {
    return new Set([this.mother, this.father]);
  }

  childrenSet() {
    return new Set(this.children.individuals);
  }
}

export class SibshipUnit extends IndividualSet {
  individuals = new Array<Individual>();

  individualSet() {
    return new Set(this.individuals);
  }

  childrenSet() {
    return new Set();
  }
}
