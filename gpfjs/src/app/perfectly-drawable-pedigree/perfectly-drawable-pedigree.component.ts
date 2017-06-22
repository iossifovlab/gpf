import { Component, OnInit, ChangeDetectionStrategy } from '@angular/core';

import { PedigreeData } from '../genotype-preview-table/genotype-preview';
import { PedigreeMockService } from './pedigree-mock.service';
import { Individual, MatingUnit, IndividualSet, ParentalUnit } from '../pedigree-chart/pedigree-data';
import {
  hasIntersection, intersection, equal, isSubset, difference
} from '../utils/sets-helper';
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

  private families: {};
  private drawInput = true;

  constructor(
    private pedigreeMockService: PedigreeMockService
  ) { }

  getMaxMatingUnitsPerIndividual(familyId: string) {
    let si =
      this.createSandwichInstance(this.families[familyId]);

    let matingUnits = si.vertices.filter(v => v instanceof MatingUnit) as MatingUnit[];
    let fathersArray = matingUnits.map(mu => mu.father);
    let mothersArray = matingUnits.map(mu => mu.mother);

    let maxMatings = Math.max(
      fathersArray.length - (new Set(fathersArray)).size + 1,
      mothersArray.length - (new Set(mothersArray)).size + 1);

    return maxMatings;
  }

  ngOnInit() {
    this.families = this.pedigreeMockService.getMockFamily();
    let allFamilies = [];
    for (let familyId in this.families) {
      if (this.families.hasOwnProperty(familyId)) {
        allFamilies.push(familyId);
      }
    }

    if (this.drawInput) {
      let maxMatings = 0;
      let moreThanTwoMatingsFamilies = [];
      for (let familyId of this.newNotPDP) {
        let currentMaxMatings = this.getMaxMatingUnitsPerIndividual(familyId);

        if (currentMaxMatings >= maxMatings) {
          console.log("Max matings of family", familyId, "is", currentMaxMatings);
          maxMatings = currentMaxMatings;
        }
        if (currentMaxMatings > 2) {
          moreThanTwoMatingsFamilies.push(familyId);
        }
        // if (fathersArray.length === (new Set(fathersArray)).size &&
        //     mothersArray.length === (new Set(mothersArray)).size) {
        //   console.log("family ", familyId, "has only sinly mated individuals");
        // }
      }
      console.log("moreThanTwoMatingsFamilies", moreThanTwoMatingsFamilies);

      console.log("left:", Array.from(difference(new Set(this.newNotPDP), new Set(moreThanTwoMatingsFamilies))));

      let otherFamilies = difference(new Set(allFamilies), new Set(this.newNotPDP));
      for (let familyId of Array.from(otherFamilies)) {
        if (this.getMaxMatingUnitsPerIndividual(familyId) > 1) {
          console.log("Family", familyId, "has more than 1 mating per individual");
        }
      }

      let [sandwichInstance, isPDP] = this.isPDP(this.families['AU1433']);

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
    } else {
      this.areAllPDP();
    }
  }

  newNotPDP = ["AU0025", "AU0110", "AU0768", "AU0931", "AU0932", "AU0985", "AU1025", "AU1245", "AU1271", "AU1373", "AU1410", "AU1500", "AU1607", "AU1608", "AU1616", "AU1619", "AU1689", "AU1921", "AU1940", "AU1952", "AU1961", "AU2136", "AU2311", "AU2720", "AU2756", "AU2837", "AU2860", "AU3344", "AU3541", "AU3618", "AU3702", "AU3766", "AU3872", "AU3889", "AU3939", "AU3973", "AU4001", "AU4033", "AU4058", "AU4138", "AU4141"];
  oldNotPDP = ["AU0025", "AU0110", "AU0455", "AU0668", "AU0768", "AU0931", "AU0932", "AU0985", "AU1025", "AU1245", "AU1271", "AU1373", "AU1410", "AU1500", "AU1607", "AU1608", "AU1616", "AU1619", "AU1689", "AU1921", "AU1940", "AU1952", "AU1961", "AU2136", "AU2311", "AU2720", "AU2756", "AU2837", "AU2860", "AU3344", "AU3541", "AU3618", "AU3702", "AU3766", "AU3872", "AU3889", "AU3939", "AU3973", "AU4001", "AU4033", "AU4058", "AU4138", "AU4141"];
  areAllPDP() {

    // console.log(subtract(new Set(this.oldNotPDP), new Set(this.newNotPDP)));
    console.log("Beginning!");
    let counter = 0;
    let notPDP = [];
    let times = [];
    let succeededTimes = [];
    for (let familyId in this.families) {
      if (this.families.hasOwnProperty(familyId)) {
        let start = Date.now()
        let [sandwichInstance, isPDP] = this.isPDP(this.families[familyId]);
        let time = start - Date.now();
        times.push([time, !!isPDP]);
        if (!isPDP) {
          // console.log("Found not perfectly drawable:");
          notPDP.push(familyId);
        } else {
          succeededTimes.push(time)
        }
        if ((counter++) % 1 === 0) {
          console.log("on family", familyId);
        }
      }
    }
    console.log("Not pdp:", notPDP);
    console.log("Times:", times.map(([time, ]) => time));
    console.log("Mean time:", times.map(a => a[0]).reduce((a, b) => a + b, 0) / times.length);
    console.log("succeeded times", succeededTimes);
    console.log("succeeded mean time", succeededTimes.reduce((a, b) => a+b, 0) / succeededTimes.length);
  }

  isPDP(family: PedigreeData[]): [SandwichInstance<Vertex>, Interval[]] {
    let sandwichInstance = this.createSandwichInstance(family);

    return [sandwichInstance, solveSandwich(sandwichInstance)];
  }

  createSandwichInstance(family: PedigreeData[]) {

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

        for (let individual of family){
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

        // console.log("sameRankEdges", sameRankEdges);
        // console.log("sameGenerationNotMateEdges", sameGenerationNotMateEdges);
        // console.log("sameGenerationNotSiblingEdges", sameGenerationNotSiblingEdges);
        // console.log("intergenerationalEdges", intergenerationalEdges);

        let requiredEdges = new Set(
          matingEdges.concat(sibshipEdges).concat(matingUnitSibshipUnitEdges));
        let forbiddenEdges = new Set(
          sameRankEdges
            .concat(sameGenerationNotMateEdges)
            .concat(sameGenerationNotSiblingEdges)
            .concat(intergenerationalEdges)
        );

        return new SandwichInstance(allVertices, requiredEdges, forbiddenEdges);
  }


}
