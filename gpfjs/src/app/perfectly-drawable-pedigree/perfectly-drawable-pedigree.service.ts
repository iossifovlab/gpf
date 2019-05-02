import { Injectable } from '@angular/core';
import { PedigreeData } from '../genotype-preview-model/genotype-preview';
import { Individual, MatingUnit, IndividualSet, ParentalUnit } from '../pedigree-chart/pedigree-data';
import { Edge as GraphEdge, Vertex as GraphVertex } from '../utils/undirected-graph';
import { hasIntersection, equal, isSubset } from '../utils/sets-helper';
import { SandwichInstance, solveSandwich, IntervalForVertex } from '../utils/interval-sandwich';


type Vertex = GraphVertex<IndividualSet>;
type Edge = GraphEdge<Vertex>;

@Injectable()
export class PerfectlyDrawablePedigreeService {

  createSandwichInstance(family: PedigreeData[]) {
    const [idsToIndividualUnit, idsToMatingUnit] = this.getIndividualsAndMatingUnitMaps(family);

    const individualVertices = this.getIndividualsFromMap(idsToIndividualUnit) as IndividualSet[];

    const matingVertices: Vertex[] = [];
    const sibshipVertices: Vertex[] = [];

    idsToMatingUnit.forEach(matingUnit => {
      matingVertices.push(matingUnit);
      if (matingUnit.children.individuals.length > 0) {
        sibshipVertices.push(matingUnit.children);
      }
    });

    const allVertices: Vertex[] = individualVertices.concat(matingVertices).concat(sibshipVertices);

    if (individualVertices.length) {
      (individualVertices[0] as Individual).addRank(0);
      this.fixRank(individualVertices as Individual[]);
    }


    // Ea-
    const sameRankEdges: Edge[] = [];
    for (let i = 0; i < individualVertices.length - 1; i++) {
      for (let j = i + 1; j < individualVertices.length; j++) {
        if (equal(individualVertices[i].generationRanks(), individualVertices[j].generationRanks())) {
          sameRankEdges.push([individualVertices[i], individualVertices[j]]);
        }
      }
    }


    // Eb+ and Eb-
    const matingEdges: Edge[] = [];
    const sameGenerationNotMateEdges: Edge[] = [];
    for (const individual of individualVertices) {
      for (const matingUnit of matingVertices) {
        if (isSubset(individual.individualSet(), matingUnit.individualSet())) {
          matingEdges.push([individual, matingUnit]);
        } else if (equal(individual.generationRanks(), matingUnit.generationRanks())) {
          sameGenerationNotMateEdges.push([individual, matingUnit]);
        }
      }
    }

    // Ec+ and Ec-
    const sibshipEdges: Edge[] = [];
    const sameGenerationNotSiblingEdges: Edge[] = [];
    for (const individual of individualVertices as Individual[]) {
      for (const sibshipUnit of sibshipVertices) {
        if (isSubset(individual.individualSet(), sibshipUnit.individualSet())) {
          sibshipEdges.push([individual, sibshipUnit]);
        } else if (equal(individual.generationRanks(), sibshipUnit.generationRanks())) {
          if (individual.parents) {
              sameGenerationNotSiblingEdges.push([individual, sibshipUnit]);
          }
        }
      }
    }



    // Ed+
    const matingUnitSibshipUnitEdges: Edge[] = [];
    for (const sibshipUnit of sibshipVertices) {
      for (const matingUnit of matingVertices) {
        if (equal(matingUnit.childrenSet(), sibshipUnit.individualSet())) {
          matingUnitSibshipUnitEdges.push([matingUnit, sibshipUnit]);
        }
      }
    }
    // console.log("matingUnitSibshipUnitEdges", matingUnitSibshipUnitEdges);

    // Ee-
    const intergenerationalEdges: Edge[] = [];
    for (const sibshipUnit of sibshipVertices.concat(matingVertices)) {
      for (const matingUnit of matingVertices) {
        if (!hasIntersection(matingUnit.generationRanks(), sibshipUnit.generationRanks())) {
          if (!hasIntersection(matingUnit.individualSet(), sibshipUnit.individualSet())) {
            if (!matingUnitSibshipUnitEdges.find(
              ([mu, sibship]) => mu === matingUnit &&
                                 sibship === sibshipUnit)) {
              intergenerationalEdges.push([matingUnit, sibshipUnit]);
            }
          }
        }
      }
    }

    const requiredEdges = new Set(
      matingEdges.concat(sibshipEdges).concat(matingUnitSibshipUnitEdges));
    const forbiddenEdges = new Set(
      sameRankEdges
        .concat(sameGenerationNotMateEdges)
        .concat(sameGenerationNotSiblingEdges)
        .concat(intergenerationalEdges)
    );

    return new SandwichInstance(allVertices, requiredEdges, forbiddenEdges);
  }

  private getIndividualsAndMatingUnitMaps(family: PedigreeData[]):
      [Map<string, Individual>, Map<string, MatingUnit>] {
    const idToNodeMap = new Map<string, Individual>();
    const idsToMatingUnit = new Map<string, MatingUnit>();

    const getOrCreateIndividual = (name) => {
      if (idToNodeMap.has(name)) {
        return idToNodeMap.get(name);
      } else {
        const individual = new Individual();
        idToNodeMap.set(name, individual);
        return individual;
      }
    };

    for (const individual of family) {
      const mother = getOrCreateIndividual(individual.mother);
      const father = getOrCreateIndividual(individual.father);
      if (mother !== father && !idsToMatingUnit.has(individual.mother + ',' + individual.father)) {
        idsToMatingUnit.set(individual.mother + ',' + individual.father, new MatingUnit(mother, father));
      }
      const parentNode = idsToMatingUnit.get(individual.mother + ',' + individual.father);

      const node = getOrCreateIndividual(individual.id);

      node.pedigreeData = individual;
      if (mother !== father) {
        node.parents = new ParentalUnit(mother, father);
      }

      if (parentNode) {
        parentNode.children.individuals.push(node);
      }
    }

    idToNodeMap.delete('0');
    idToNodeMap.delete('');

    return [idToNodeMap, idsToMatingUnit];
  }

  private getIndividualsFromMap(idToNodeMap: Map<string, Individual>) {
    const individualVertices: Individual[] = [];
    idToNodeMap.forEach(individual => {
      individualVertices.push(individual);
    });

    return individualVertices;
  }

  getIndividuals(family: PedigreeData[]) {
    const idToNodeMap = this.getIndividualsAndMatingUnitMaps(family)[0];

    return this.getIndividualsFromMap(idToNodeMap);
  }

  isPDP(family: PedigreeData[]) {
    const start = Date.now();
    const sandwichInstance = this.createSandwichInstance(family);
    const result: [SandwichInstance<Vertex>, IntervalForVertex<Vertex>[]] =
      [sandwichInstance, solveSandwich(sandwichInstance)] ;

    console.warn('isPDP took', Date.now() - start, 'ms');

    return result;

  }

  fixRank(intervals: Array<Individual>) {
    if (!intervals) {
      return intervals;
    }

    const maxRank = intervals.map(interval => interval.rank)
      .reduce((acc, current) => Math.max(acc, current), 0);

    return intervals.map(interval => {
      interval.rank -= maxRank;
      interval.rank = -interval.rank;
      return interval;
    });
  }

}
