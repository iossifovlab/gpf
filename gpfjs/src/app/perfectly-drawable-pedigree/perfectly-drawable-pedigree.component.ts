import { Component, OnInit, ChangeDetectionStrategy } from '@angular/core';

import { PedigreeData } from '../genotype-preview-table/genotype-preview';
import { PedigreeMockService } from './pedigree-mock.service';
import { Individual, MatingUnit, IndividualSet, ParentalUnit } from '../pedigree-chart/pedigree-data';
import { hasIntersection, intersection, equal, isSubset } from '../utils/sets-helper';
import { Edge as GraphEdge, Vertex as GraphVertex } from '../utils/undirected-graph';

import { SandwichInstance, solveSandwich, Interval } from '../utils/interval-sandwich';

type Vertex = GraphVertex<IndividualSet>;
type Edge = GraphEdge<Vertex>;

declare var vis: any;

@Component({
  selector: 'gpf-perfectly-drawable-pedigree',
  templateUrl: './perfectly-drawable-pedigree.component.html',
  styleUrls: ['./perfectly-drawable-pedigree.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class PerfectlyDrawablePedigreeComponent implements OnInit {

  private family: PedigreeData[];

  constructor(
    private pedigreeMockService: PedigreeMockService
  ) { }

  ngOnInit() {
    this.family = this.pedigreeMockService.getMockFamily();

    let [sandwichInstance, isPDP] = this.isPDP();

    let container = document.getElementById('visualization');


    let itemsData = [];
    for (let vertex of sandwichInstance.vertices) {
      itemsData.push({
        id: vertex.toString() + vertex.constructor.name,
        label: vertex.constructor.name + " (" + vertex.toString() + ")/" + Array.from(vertex.generationRanks()).join(",")
      });
    }
    let items = new vis.DataSet(itemsData);

    let edgesData = [];
    for (let edge of Array.from(sandwichInstance.required)) {
      edgesData.push({
        from: edge[0].toString() + edge[0].constructor.name,
        to: edge[1].toString() + edge[1].constructor.name,
        scaling: {
          min: 10,
          max: 30
        },
        color: {
          color: "#e23f4d"
        }
      });
    }
    for (let edge of Array.from(sandwichInstance.forbidden)) {
      edgesData.push({
        from: edge[0].toString() + edge[0].constructor.name,
        to: edge[1].toString() + edge[1].constructor.name,
        dashes: true,
        physics: false,
        color: {
          opacity: 0.4
        }
      });
    }
    let edges = new vis.DataSet(edgesData);

    let data = {
      nodes: items,
      edges: edges
    };

    // Configuration for the Timeline
    let options = {};

    // Create a Timeline
    let timeline = new vis.Network(container, data, options);
  }

  isPDP(): [SandwichInstance<Vertex>, Interval[]] {

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
      if (mother !== father && !idsToMatingUnit.has(individual.mother + ',' + individual.father)) {
        idsToMatingUnit.set(individual.mother + ',' + individual.father, new MatingUnit(mother, father));
      }
      let parentNode = idsToMatingUnit.get(individual.mother + ',' + individual.father);

      let node = getOrCreateIndividual(individual.id);

      node.pedigreeData = individual;
      if (mother && father) {
        node.parents = new ParentalUnit(mother, father);
      }

      if (parentNode) {
        parentNode.children.individuals.push(node);
      }
    }

    let individualVertices: Vertex[] = [];
    idToNodeMap.delete('0');
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
    for (let i = 0; i < individualVertices.length - 1; i++) {
      for (let j = i + 1; j < individualVertices.length; j++) {
        if (equal(individualVertices[i].generationRanks(), individualVertices[j].generationRanks())) {
          sameRankEdges.push([individualVertices[i], individualVertices[j]]);
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

    console.log("sameRankEdges", sameRankEdges);
    console.log("sameGenerationNotMateEdges", sameGenerationNotMateEdges);
    console.log("sameGenerationNotSiblingEdges", sameGenerationNotSiblingEdges);
    console.log("intergenerationalEdges", intergenerationalEdges);

    let requiredEdges = new Set(matingEdges.concat(sibshipEdges).concat(matingUnitSibshipUnitEdges));
    let forbiddenEdges = new Set(sameRankEdges.concat(sameGenerationNotMateEdges)
      .concat(sameGenerationNotSiblingEdges).concat(intergenerationalEdges));

    let sandwichInstance =
      new SandwichInstance(allVertices, requiredEdges, forbiddenEdges);

    return [sandwichInstance, solveSandwich(sandwichInstance)];
  }


}
