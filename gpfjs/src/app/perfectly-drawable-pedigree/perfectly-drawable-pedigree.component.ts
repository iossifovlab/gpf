import { Component, OnInit } from '@angular/core';

import { PedigreeData } from '../genotype-preview-table/genotype-preview';
import { PedigreeMockService } from './pedigree-mock.service';
import { Individual, MatingUnit, IndividualSet, ParentalUnit } from '../pedigree-chart/pedigree-data';

type Vertex = IndividualSet;
type Edge = [Vertex, Vertex];

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

    let individualVertices = [];
    idToNodeMap.forEach(individual => {
      individualVertices.push(individual);
    });


    let matingVertices = [];
    let sibshipVertices = [];
    idsToMatingUnit.forEach(matingUnit => {
      matingVertices.push(matingUnit);
      if (matingUnit.children.individuals.length > 0) {
        sibshipVertices.push(matingUnit.children);
      }
    });

    let allVertices: Vertex[] = individualVertices.concat(matingVertices).concat(sibshipVertices);

    if (individualVertices.length) {
      individualVertices[0].addRank(0);
    }


    // Ea-
    let sameRankEdges: Edge[] = [];
    for (let i = 0; i < allVertices.length - 1; i++) {
      for (let j = i + 1; j < allVertices.length; j++) {
        if (this.equal(allVertices[i].generationRanks(), allVertices[j].generationRanks())) {
          sameRankEdges.push([allVertices[i], allVertices[j]]);
        }
      }
    }
    console.log(sameRankEdges);

  }

  equal(setA: Set<number>, setB: Set<number>) {
    if (setA.size !== setB.size) {
      return false;
    }
    for (let a of Array.from(setA)) {
      if (!setB.has(a)) {
        return false;
      }
    }
    return true;
  }

}
