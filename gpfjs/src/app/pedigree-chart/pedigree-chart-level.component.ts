import { Input, Component, OnInit } from '@angular/core';
import { PedigreeData } from '../genotype-preview-table/genotype-preview';
import { Individual, IndividualWithPosition, Line, SameLevelGroup } from './pedigree-data';

@Component({
  selector: '[gpf-pedigree-chart-level]',
  templateUrl: './pedigree-chart-level.component.html'
})
export class PedigreeChartLevelComponent implements OnInit {
  pedigreeDataWithLayout: IndividualWithPosition[];
  lines: Line[];

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

  private optimizeDrawing(groups: SameLevelGroup[][]) {
    for (let i = groups.length - 1; i > 0; i--) {
      let onlySiblingsGroup = this.groups[i]
        .filter(group => group.members.some(member => !!member.parents));
      for (let group of onlySiblingsGroup) {
        this.centerParentOfGroup(groups, group);
      }
    }
  }

  private centerParentOfGroup(groups: SameLevelGroup[][], group: SameLevelGroup) {
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
      } else if (!individual.areInMatingUnit(currentGroup.lastMember) &&
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
    if (groups.length !== 1) {
      console.log(groups.length, groups);
    }

    for (let group of groups) {
      group.startX = xOffset;
      group.gapSize = maxGap;
      group.memberSize = memberSize;
      xOffset += group.width + maxGap * 2;
    }

    return groups;
  }

  private overlapOnLayer(groups: SameLevelGroup[]) {
    let individuals: IndividualWithPosition[] = [];

    for (let group of groups) {
      individuals = individuals.concat(group.individualsWithPositions);
    }
    for (let i = 0; i < individuals.length - 1; i++) {
      let difference = Math.abs(
        individuals[i].xCenter - individuals[i + 1].xCenter);
      if (difference < individuals[i].size / 2 ||
          difference < individuals[i + 1].size / 2) {
        return true;
      }
    }

    return false;
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

          if (current.individual.areInMatingUnit(other.individual)) {
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
