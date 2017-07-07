import { Input, Component, OnInit } from '@angular/core';

import { PedigreeData } from '../genotype-preview-table/genotype-preview';
import { Individual, IndividualWithPosition, Line, SameLevelGroup, MatingUnit, ParentalUnit } from './pedigree-data';
import { hasIntersection } from '../utils/sets-helper';

@Component({
  selector: '[gpf-pedigree-chart-level]',
  templateUrl: './pedigree-chart-level.component.html'
})
export class PedigreeChartLevelComponent implements OnInit {
  pedigreeDataWithLayout: IndividualWithPosition[];
  lines: Line[];
  blownFuse = false;

  @Input() connectingLineYPosition: number;
  @Input() individuals: Individual[][];
  groups: SameLevelGroup[][] = new Array<SameLevelGroup[]>();
  private individualToGroup: Map<string, SameLevelGroup> = new Map();

  ngOnInit() {
    this.pedigreeDataWithLayout = [];
    this.lines = [];

    if (this.individuals) {
      for (let i = 0; i < this.individuals.length; i++) {
        this.groups.push(
          this.generateLayout(this.individuals[i], i));
      }
      this.optimizeDrawing(this.groups);
      for (let group of this.groups) {
        this.lines = this.lines.concat(
          this.generateLines(group));
      }
    }

    this.pedigreeDataWithLayout = this.groups
      .map(g => g.map(g1 => g1.individualsWithPositions)
        .reduce((acc, individuals) => acc.concat(individuals), []))
        .reduce((acc, individuals) => acc.concat(individuals), []);

  }

  private optimizeDrawing(groups: SameLevelGroup[][], xOffset = 20) {
    for (let i = groups.length - 1; i > 0; i--) {
      let onlySiblingsGroup = this.groups[i]
        .filter(group => group.members.some(member => !!member.parents));
      for (let group of onlySiblingsGroup) {
        this.centerParentsOfGroup(group);
      }
    }

    for (let i = 0; i < groups.length - 1; i++) {
      let onlyMatingGroups = this.groups[i]
        .filter(group => group.members.some(member => member.matingUnits.length > 0));
      for (let group of onlyMatingGroups) {
        this.centerChildrenOfParents(group);
      }
    }

    this.fixOverlaps(groups);
    this.moveGroupsToLeft(groups, xOffset);

  }

  private fixOverlaps(groups: SameLevelGroup[][]) {
    let currentIter = 0;

    let movedGroups: SameLevelGroup[] = [];
    for (let i = 0; i < groups.length; i++) {
      currentIter++;
      if (currentIter > 1000) {
        console.log("Exit due to max iter!");
        this.blownFuse = true;
        // debugger
        return;
      }
      // movedGroups = [];
      let overlaps = this.overlappingGroupsOnLevel(groups[i]);
      if (overlaps.length) {
        let [group1, group2] = overlaps[0];
        let g1OldX = group1.startX;
        let g2OldX = group2.startX;


        let childrenStartAndEnd1 =
          this.getFirstAndLastChildWithPositions(group1);
        let childrenStartAndEnd2 =
          this.getFirstAndLastChildWithPositions(group2);

        let g1Width = group1.width * 2;
        if (childrenStartAndEnd1[0]) {
          g1Width = childrenStartAndEnd1[1].xUpperLeftCorner -
          childrenStartAndEnd1[0].xUpperLeftCorner + group1.memberSize;
        }
        let g2Width = group2.width * 2;
        if (childrenStartAndEnd2[0]) {
          g2Width = childrenStartAndEnd2[1].xUpperLeftCorner -
          childrenStartAndEnd2[0].xUpperLeftCorner + group2.memberSize;
        }

        // g1Width = Math.abs(g1Width);
        // g2Width = Math.abs(g2Width);

        // console.log(g1Width, g2Width);


        let group1Center = group1.startX + g1Width / 2;
        let group2Center = group2.startX + g2Width / 2;

        let g1NewX = group1Center - g1Width + group1.memberSize / 2;
        let g2NewX = group2Center - group2.memberSize / 2;

        group1.startX = g1NewX;
        // console.log(g1NewX, g2NewX);
        // console.log("First")

        if (this.groupsOverlap(group1, group2)) {
          group1.startX = g1OldX;
          group2.startX = g2NewX;
          // console.log("Second")
        } else {
          // this.centerChildrenOfParents(group1);
          i--;
          continue;
        }

        if (this.groupsOverlap(group1, group2)) {
          group1.startX = g1NewX;
          group2.startX = g2NewX;
          // console.log("Third")
        } else {
          // this.centerChildrenOfParents(group2);
          i--;
          continue;
        }

        if (this.groupsOverlap(group1, group2)) {
            group1.startX = g1OldX;
            group2.startX = g2OldX;
            // console.log("Reset")
        } else {
          // this.centerChildrenOfParents(group1);
          // this.centerChildrenOfParents(group2);
        }
      }
      // for (let [group1, group2] of overlaps) {
      //   if (movedGroups.indexOf(group1) === -1) {
      //     let group1Parents = this.getParentsGroups(group1);
      //     let group2Parents = this.getParentsGroups(group2);
      //
      //     if (group1Parents.length === 1 && group2Parents.length === 1 &&
      //         group1Parents[0] === group2Parents[0]) {
      //       group2.startX = group1.startX + group1.width + 8;
      //
      //
      //     }
      //   }
      //   movedGroups.push(group2);
      //   i--;
      // }
    }
  }

  // private findMatingChain(group: SameLevelGroup) {
  //   let matingChains: [IndividualWithPosition, IndividualWithPosition][] = [];
  //   let individuals = group.individualsWithPositions;
  //
  //   for (let i = 0; i < individuals.length - 1; i++) {
  //     if (individuals[i].individual.matingUnits.length > 0) {
  //       let start = i;
  //       for (let j = i + 1; j < individuals.length; j++) {
  //         let prevMatingUnits = new Set(individuals[j - 1].individual.matingUnits);
  //         let currentMatingUnits = new Set(individuals[j].individual.matingUnits);
  //         if (!hasIntersection(prevMatingUnits, currentMatingUnits)) {
  //           matingChains.push([individuals[start], individuals[j]]);
  //           break;
  //         }
  //       }
  //     }
  //   }
  //
  //   return matingChains;
  // }

  private getParentsGroups(childrenGroup: SameLevelGroup) {
    let parents: ParentalUnit[] = childrenGroup.members
      .filter(i => !!i.parents)
      .map(i => i.parents);
    parents = Array.from(new Set(parents));

    return parents
      .map(parentalUnit => this.individualToGroup.get(parentalUnit.mother.pedigreeData.id));
  }

  private moveGroupsToLeft(groups: SameLevelGroup[][], xOffset) {
    let minStartXReducer = (g1, g2) => g1.startX < g2.startX ? g1 : g2;

    let leftmostGroupX = groups
      .map(group => group.reduce(minStartXReducer).startX)
      .reduce((a, b) => Math.min(a, b));

    let toMove = leftmostGroupX - xOffset;
    groups.forEach(g => g.forEach(group => group.startX -= toMove));
  }

  private centerChildrenOfParents(group: SameLevelGroup) {
    let groupMatingUnits = group.members
      .filter(member => member.matingUnits.length > 0)
      .map(member => member.matingUnits)
      .reduce((acc, matingUnits) => acc.concat(matingUnits), []);

    groupMatingUnits = Array.from(new Set(groupMatingUnits));

    for (let matingUnit of groupMatingUnits) {
      let fatherX = group.getXForMember(matingUnit.father);
      let motherX = group.getXForMember(matingUnit.mother);

      let middle = (fatherX + motherX) / 2;

      let childrenGroup = this.individualToGroup
        .get(matingUnit.children.individuals[0].pedigreeData.id);

      let childrenStartAndEnd =
        this.getFirstAndLastChildWithPositions(childrenGroup, matingUnit);

      let width = childrenStartAndEnd[1].xUpperLeftCorner -
        childrenStartAndEnd[0].xUpperLeftCorner;
      let startOffset = childrenGroup.startX - childrenStartAndEnd[0].xCenter;

      childrenGroup.startX = middle - width / 2 + startOffset;
    }
  }

  private getFirstAndLastChildWithPositions(children: SameLevelGroup,
    matingUnit?: MatingUnit) {
    return children.individualsWithPositions
      .reduce((acc, m) => {
        if (matingUnit) {
          if (m.individual.isChildOf(matingUnit.father, matingUnit.mother)) {
            if (!acc[0]) {
              acc[0] = m;
            }
            acc[1] = m;
          }
          return acc;
        }
        if (m.individual.parents) {
          if (!acc[0]) {
            acc[0] = m;
          }
          acc[1] = m;
        }
        return acc;
      }, [null, null] as [IndividualWithPosition, IndividualWithPosition] );
  }

  private centerParentsOfGroup(group: SameLevelGroup) {
      let firstMember = group.members.find(individual => !!individual.parents);
      if (!this.individualToGroup.has(firstMember.pedigreeData.id)) {
        return;
      }
      let parentGroup = this.individualToGroup
        .get(firstMember.parents.father.pedigreeData.id);

      parentGroup.startX = group.startX + group.width / 2 - parentGroup.width / 2;
  }

  private getGroupsForLevel(individuals: Individual[], level, totalHeight = 30) {
    let groups: SameLevelGroup[] = new Array<SameLevelGroup>();
    let currentGroup: SameLevelGroup;

    for (let individual of individuals) {
      if (!currentGroup) {
        currentGroup = new SameLevelGroup(totalHeight * level + 20);
        currentGroup.members.push(individual);
        groups.push(currentGroup);
      } else if (!individual.areMates(currentGroup.lastMember) &&
        (!individual.areSiblings(currentGroup.lastMember))) {
        currentGroup = new SameLevelGroup(totalHeight * level + 20);
        currentGroup.members.push(individual);
        groups.push(currentGroup);
      } else {
        currentGroup.members.push(individual);
      }
      this.individualToGroup.set(individual.pedigreeData.id, currentGroup);
    }

    return groups;
  }

  private generateLayout(individuals: Individual[], level: number,
    memberSize = 21, maxGap = 8, totalHeight = 30, xOffset = 20) {
    let groups = this.getGroupsForLevel(individuals, level);

    for (let group of groups) {
      group.startX = xOffset;
      group.gapSize = maxGap;
      group.memberSize = memberSize;
      xOffset += group.width + maxGap * 2;
    }

    return groups;
  }

  private groupsOverlap(group1: SameLevelGroup, group2: SameLevelGroup) {
    let inside = (g1, g2) => g1.startX <= g2.startX &&
      g1.startX + g1.width >= g2.startX;
    return inside(group1, group2) || inside(group2, group1);
  }

  private overlappingGroupsOnLevel(groups: SameLevelGroup[]) {
    let individuals: IndividualWithPosition[] = [];
    let overlappingGroups: [SameLevelGroup, SameLevelGroup][] = [];

    for (let i = 0; i < groups.length - 1; i++) {
      if (this.groupsOverlap(groups[i], groups[i + 1])) {
        overlappingGroups.push([groups[i], groups[i + 1]]);
      }
      // individuals = individuals.concat(group.individualsWithPositions);
    }
    // for (let i = 0; i < individuals.length - 1; i++) {
    //   let firstIndividual = individuals[i];
    //   let secondIndividual = individuals[i + 1];
    //
    //   if (firstIndividual.xCenter > secondIndividual.xCenter) {
    //     let temp = firstIndividual;
    //     firstIndividual = secondIndividual;
    //     secondIndividual = firstIndividual;
    //   }
    //
    //   let difference = secondIndividual.xCenter - firstIndividual.xCenter;
    //   console.log(difference);
    //   if (difference < firstIndividual.size / 2 ||
    //       difference < secondIndividual.size / 2) {
    //
    //     if (this.individualToGroup.get(firstIndividual.individual.pedigreeData.id) ===
    //       this.individualToGroup.get(secondIndividual.individual.pedigreeData.id)) {
    //         console.log("BAD!");
    //       }
    //
    //     overlappingGroups.push([
    //       this.individualToGroup.get(firstIndividual.individual.pedigreeData.id),
    //       this.individualToGroup.get(secondIndividual.individual.pedigreeData.id),
    //     ]);
    //   }
    // }

    return overlappingGroups;
  }

  private generateLines(pedigreeData: SameLevelGroup[], horizontalYOffset = 15) {
    let lines = new Array<Line>();


    for (let group of pedigreeData) {
      let lineY = group.yCenter - horizontalYOffset;
      let individuals = group.individualsWithPositions;

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
            lines.push(new Line(middleX, current.yCenter, middleX, group.yCenter + horizontalYOffset));
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


    }


    return lines;
  }
}
