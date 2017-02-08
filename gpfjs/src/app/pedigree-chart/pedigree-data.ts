import { PedigreeData } from '../genotype-preview-table/genotype-preview';

export class Individual {
  matingUnits = new Array<MatingUnit>();
  pedigreeData: PedigreeData;
}

export class MatingUnit {
  children = new SibshipUnit();
  visited = false;

  constructor(
    readonly mother: Individual,
    readonly father: Individual
  ) {
    mother.matingUnits.push(this);
    console.log("Pushing Mother");

    father.matingUnits.push(this);
    console.log("Pushing Father");
  }
}

export class SibshipUnit {
  individuals = new Array<Individual>();
}
