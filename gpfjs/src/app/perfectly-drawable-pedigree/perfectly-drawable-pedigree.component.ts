import { Component, OnInit } from '@angular/core';

import { PedigreeData } from '../genotype-preview-table/genotype-preview';
import { PedigreeMockService } from './pedigree-mock.service';
import { Individual, MatingUnit, IndividualSet, ParentalUnit } from '../pedigree-chart/pedigree-data';
import { hasIntersection, intersection, equal, isSubset } from '../utils/sets-helper';

import { SandwichInstance, solveSandwich } from './interval-sandwich';

export type Vertex = IndividualSet;
export type Edge = [Vertex, Vertex];

@Component({
  selector: 'gpf-perfectly-drawable-pedigree',
  templateUrl: './perfectly-drawable-pedigree.component.html',
  styleUrls: ['./perfectly-drawable-pedigree.component.css']
})
export class PerfectlyDrawablePedigreeComponent implements OnInit {

  private family: PedigreeData[];

  constructor(
    private pedigreeMockService: PedigreeMockService
  ) { }

  ngOnInit() {
    this.family = this.pedigreeMockService.getMockFamily();
  }

  isPDP() {
    if (!this.family) {
      return false;
    }


    let idToNodeMap = new Map<string, Individual>();
    let idsToMatingUnit = new Map<string, MatingUnit>();

    let getOrCreateIndividual = (name) => {
      if (idToNodeMap.has(name)) {
        return idToNodeMap.get(name);
      } else {
        let individual = new Individual();
        idToNodeMap.set(name, individual);
        return individual;
      }
    };

    for (let individual of this.family){
      let mother = getOrCreateIndividual(individual.mother);
      let father = getOrCreateIndividual(individual.father);
      if (!idsToMatingUnit.has(individual.mother + ',' + individual.father)) {
        idsToMatingUnit.set(individual.mother + ',' + individual.father, new MatingUnit(mother, father));
      }
      let parentNode = idsToMatingUnit.get(individual.mother + ',' + individual.father);

      let node = getOrCreateIndividual(individual.id);

      node.pedigreeData = individual;
      node.parents = new ParentalUnit(mother, father);

      parentNode.children.individuals.push(node);
    }

    let individualVertices: Vertex[] = [];
    idToNodeMap.forEach(individual => {
      individualVertices.push(individual);
    });


    let matingVertices: Vertex[] = [];
    let sibshipVertices: Vertex[] = [];
    idsToMatingUnit.forEach(matingUnit => {
      matingVertices.push(matingUnit);
      if (matingUnit.children.individuals.length > 0) {
        sibshipVertices.push(matingUnit.children);
      }
    });

    let allVertices: Vertex[] = individualVertices.concat(matingVertices).concat(sibshipVertices);

    if (individualVertices.length) {
      (individualVertices[0] as Individual).addRank(0);
    }


    // Ea-
    let sameRankEdges: Edge[] = [];
    for (let i = 0; i < allVertices.length - 1; i++) {
      for (let j = i + 1; j < allVertices.length; j++) {
        if (equal(allVertices[i].generationRanks(), allVertices[j].generationRanks())) {
          sameRankEdges.push([allVertices[i], allVertices[j]]);
        }
      }
    }

    // Eb+ and Eb-
    let matingEdges: Edge[] = [];
    let sameGenerationNotMateEdges: Edge[] = [];
    for (let individual of individualVertices) {
      for (let matingUnit of matingVertices) {
        if (isSubset(individual.individualSet(), matingUnit.individualSet())) {
          matingEdges.push([individual, matingUnit]);
        } else if (equal(individual.generationRanks(), matingUnit.generationRanks())) {
          sameGenerationNotMateEdges.push([individual, matingUnit]);
        }
      }
    }

    // Ec+ and Ec-
    let sibshipEdges: Edge[] = [];
    let sameGenerationNotSiblingEdges: Edge[] = [];
    for (let individual of individualVertices) {
      for (let sibshipUnit of sibshipVertices) {
        if (isSubset(individual.individualSet(), sibshipUnit.individualSet())) {
          sibshipEdges.push([individual, sibshipUnit]);
        } else if (equal(individual.generationRanks(), sibshipUnit.generationRanks())) {
          sameGenerationNotSiblingEdges.push([individual, sibshipUnit]);
        }
      }
    }

    // Ed+
    let matingUnitSibshipUnitEdges: Edge[] = [];
    for (let sibshipUnit of sibshipVertices) {
      for (let matingUnit of matingVertices) {
        if (equal(matingUnit.childrenSet(), sibshipUnit.individualSet())) {
          matingUnitSibshipUnitEdges.push([matingUnit, sibshipUnit]);
        }
      }
    }
    // console.log("matingUnitSibshipUnitEdges", matingUnitSibshipUnitEdges);

    // Ee-
    let intergenerationalEdges: Edge[] = [];
    for (let sibshipUnit of sibshipVertices) {
      for (let matingUnit of matingVertices) {
        if (hasIntersection(matingUnit.generationRanks(), sibshipUnit.generationRanks())) {
          if (!hasIntersection(matingUnit.individualSet(), sibshipUnit.individualSet())) {
            intergenerationalEdges.push([matingUnit, sibshipUnit]);
          }
        }
      }
    }

    let requiredEdges = new Set(matingEdges.concat(sibshipEdges).concat(matingUnitSibshipUnitEdges));
    let forbiddenEdges = new Set(sameRankEdges.concat(sameGenerationNotMateEdges)
      .concat(sameGenerationNotSiblingEdges).concat(intergenerationalEdges));

    let sandwichInstance =
      new SandwichInstance(allVertices, requiredEdges, forbiddenEdges);

    console.log(solveSandwich(sandwichInstance));
  }


}
