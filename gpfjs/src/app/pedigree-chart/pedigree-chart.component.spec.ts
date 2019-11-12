import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { ChangeDetectorRef } from '@angular/core';

import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { PedigreeChartComponent } from './pedigree-chart.component';
import { PedigreeChartMemberComponent } from './pedigree-chart-member.component';
import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';
import { PerfectlyDrawablePedigreeService } from 'app/perfectly-drawable-pedigree/perfectly-drawable-pedigree.service';
import { ResizeService } from 'app/table/resize.service';

const FAMILY_WITH_POSITIONS = [
  new PedigreeData('f1', 'prb1', 'dad1', 'mom1', 'M', 'prb',
                   '#E35252', [75, 100], false, 'label', 'sl'),
  new PedigreeData('f1', 'dad1', '', '', 'M', 'dad', '#E0E0E0',
                   [50, 50], true, 'label', 'sl'),
  new PedigreeData('f1', 'mom1', '', '', 'F', 'mom', '#FFFFFF',
                   [100, 50], false, 'label', 'sl')
];

const FAMILY_WITHOUT_POSITIONS = [
  new PedigreeData('f2', 'prb2', 'dad2', 'mom2', 'M', 'prb',
                   '#E35252', null, false, 'label', 'sl'),
  new PedigreeData('f2', 'dad2', '', '', 'M', 'dad', '#E0E0E0',
                   null, true, 'label', 'sl'),
  new PedigreeData('f2', 'mom2', '', '', 'F', 'mom', '#FFFFFF',
                   null, false, 'label', 'sl')
];

describe('PedigreeChartComponent', () => {
  let component: PedigreeChartComponent;
  let fixture: ComponentFixture<PedigreeChartComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [
        PedigreeChartComponent,
        PedigreeChartMemberComponent
      ],
      imports: [
        NgbModule.forRoot(),
      ],
      providers: [
        PerfectlyDrawablePedigreeService,
        ResizeService,
        ChangeDetectorRef
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PedigreeChartComponent);
    component = fixture.componentInstance;
  });

  it('should be created', () => {
    component.family = FAMILY_WITH_POSITIONS;
    fixture.detectChanges();

    expect(component).toBeTruthy();
  });

  it('should create lines', () => {
    component.family = FAMILY_WITH_POSITIONS;
    fixture.detectChanges();

    expect(component.straightLines.length).toBe(3);
    expect(component.curveLines.length).toBe(0);
  });

  it('should scale svg', () => {
    component.family = FAMILY_WITH_POSITIONS;
    fixture.detectChanges();

    component.scaleSvg();
    expect(component.scale).toBe(1);
  });

  it('should toggle maximized', () => {
    component.family = FAMILY_WITH_POSITIONS;
    fixture.detectChanges();

    expect(component.maximized).toBe(false);
    component.toggleMaximize();
    expect(component.maximized).toBe(true);
    component.toggleMaximize();
    expect(component.maximized).toBe(false);
  });

  it('should return view box', () => {
    component.family = FAMILY_WITH_POSITIONS;
    fixture.detectChanges();

    expect(component.getViewBox()).toBe('-8 0 81 81');
  });

  it('should load pedigree with positions', () => {
    component.family = FAMILY_WITH_POSITIONS;
    fixture.detectChanges();

    component.maximized = true;

    component.ngOnInit();

    expect(component.positionedIndividuals.length).toBe(2);

    expect(component.positionedIndividuals[0].length).toBe(2);

    expect(component.positionedIndividuals[0][0].individual.matingUnits.length).toBe(1);
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.individuals.length).toBe(1);
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.individuals[0].pedigreeData.id).toBe('prb1');
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.toString()).toBe('s{prb1}');
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.individualSet().size).toBe(1);
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.childrenSet()).toEqual(new Set());
    expect(component.positionedIndividuals[0][0].individual.pedigreeData.id).toBe('dad1');
    expect(component.positionedIndividuals[0][0].individual.parents).toBe(undefined);
    expect(component.positionedIndividuals[0][0].individual.rank).toBe(-3673473456);
    expect(component.positionedIndividuals[0][0].xCenter).toBe(11.5);
    expect(component.positionedIndividuals[0][0].yCenter).toBe(11.5);
    expect(component.positionedIndividuals[0][0].size).toBe(21.0);
    expect(component.positionedIndividuals[0][0].scaleFactor).toBe(1.0);
    expect(component.positionedIndividuals[0][0].xUpperLeftCorner).toBe(1);
    expect(component.positionedIndividuals[0][0].yUpperLeftCorner).toBe(1);

    expect(component.positionedIndividuals[0][1].individual.matingUnits.length).toBe(1);
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.individuals.length).toBe(1);
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.individuals[0].pedigreeData.id).toBe('prb1');
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.toString()).toBe('s{prb1}');
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.individualSet().size).toBe(1);
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.childrenSet()).toEqual(new Set());
    expect(component.positionedIndividuals[0][1].individual.pedigreeData.id).toBe('mom1');
    expect(component.positionedIndividuals[0][1].individual.parents).toBe(undefined);
    expect(component.positionedIndividuals[0][1].individual.rank).toBe(-3673473456);
    expect(component.positionedIndividuals[0][1].xCenter).toBe(61.5);
    expect(component.positionedIndividuals[0][1].yCenter).toBe(11.5);
    expect(component.positionedIndividuals[0][1].size).toBe(21.0);
    expect(component.positionedIndividuals[0][1].scaleFactor).toBe(1.0);
    expect(component.positionedIndividuals[0][1].xUpperLeftCorner).toBe(51);
    expect(component.positionedIndividuals[0][1].yUpperLeftCorner).toBe(1);

    expect(component.positionedIndividuals[1].length).toBe(1);
    expect(component.positionedIndividuals[1][0].individual.matingUnits.length).toBe(0);
    expect(component.positionedIndividuals[1][0].individual.pedigreeData.id).toBe('prb1');
    expect(component.positionedIndividuals[1][0].individual.parents.father.pedigreeData.id).toBe('dad1');
    expect(component.positionedIndividuals[1][0].individual.parents.mother.pedigreeData.id).toBe('mom1');
    expect(component.positionedIndividuals[1][0].individual.rank).toBe(-3673473456);
    expect(component.positionedIndividuals[1][0].xCenter).toBe(36.5);
    expect(component.positionedIndividuals[1][0].yCenter).toBe(61.5);
    expect(component.positionedIndividuals[1][0].size).toBe(21.0);
    expect(component.positionedIndividuals[1][0].scaleFactor).toBe(1.0);
    expect(component.positionedIndividuals[1][0].xUpperLeftCorner).toBe(26);
    expect(component.positionedIndividuals[1][0].yUpperLeftCorner).toBe(51);

    expect(component.lines.length).toBe(3);

    expect(component.lines[0].startX).toBe(11.5);
    expect(component.lines[0].startY).toBe(11.5);
    expect(component.lines[0].endX).toBe(61.5);
    expect(component.lines[0].endY).toBe(11.5);
    expect(component.lines[0].curved).toBe(false);
    expect(component.lines[0].curvedBaseHeight).toBeNaN();

    expect(component.lines[1].startX).toBe(36.5);
    expect(component.lines[1].startY).toBe(11.5);
    expect(component.lines[1].endX).toBe(36.5);
    expect(component.lines[1].endY).toBe(26.5);
    expect(component.lines[1].curved).toBe(false);
    expect(component.lines[1].curvedBaseHeight).toBeNaN();

    expect(component.lines[2].startX).toBe(36.5);
    expect(component.lines[2].startY).toBe(61.5);
    expect(component.lines[2].endX).toBe(36.5);
    expect(component.lines[2].endY).toBe(46.5);
    expect(component.lines[2].curved).toBe(false);
    expect(component.lines[2].curvedBaseHeight).toBeNaN();

    expect(component.pedigreeDataWithLayout.length).toBe(3);
    expect(component.pedigreeDataWithLayout[0].individual.pedigreeData.id).toBe('dad1');
    expect(component.pedigreeDataWithLayout[1].individual.pedigreeData.id).toBe('mom1');
    expect(component.pedigreeDataWithLayout[2].individual.pedigreeData.id).toBe('prb1');

    expect(component.width).toBe(73);
    expect(component.height).toBe(73);
  });

  it('should load pedigree without positions', () => {
    component.family = FAMILY_WITHOUT_POSITIONS;

    component.ngOnInit();

    expect(component.positionedIndividuals.length).toBe(2);

    expect(component.positionedIndividuals[0].length).toBe(2);

    expect(component.positionedIndividuals[0][0].individual.matingUnits.length).toBe(1);
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.individuals.length).toBe(1);
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.individuals[0].pedigreeData.id).toBe('prb2');
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.toString()).toBe('s{prb2}');
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.individualSet().size).toBe(1);
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.childrenSet()).toEqual(new Set());
    expect(component.positionedIndividuals[0][0].individual.pedigreeData.id).toBe('mom2');
    expect(component.positionedIndividuals[0][0].individual.parents).toBe(undefined);
    expect(component.positionedIndividuals[0][0].individual.rank).toBe(0);
    expect(component.positionedIndividuals[0][0].xCenter).toBe(20);
    expect(component.positionedIndividuals[0][0].yCenter).toBe(20);
    expect(component.positionedIndividuals[0][0].size).toBe(21.0);
    expect(component.positionedIndividuals[0][0].scaleFactor).toBe(1.0);
    expect(component.positionedIndividuals[0][0].xUpperLeftCorner).toBe(9.5);
    expect(component.positionedIndividuals[0][0].yUpperLeftCorner).toBe(9.5);

    expect(component.positionedIndividuals[0][1].individual.matingUnits.length).toBe(1);
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.individuals.length).toBe(1);
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.individuals[0].pedigreeData.id).toBe('prb2');
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.toString()).toBe('s{prb2}');
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.individualSet().size).toBe(1);
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.childrenSet()).toEqual(new Set());
    expect(component.positionedIndividuals[0][1].individual.pedigreeData.id).toBe('dad2');
    expect(component.positionedIndividuals[0][1].individual.parents).toBe(undefined);
    expect(component.positionedIndividuals[0][1].individual.rank).toBe(0);
    expect(component.positionedIndividuals[0][1].xCenter).toBe(49);
    expect(component.positionedIndividuals[0][1].yCenter).toBe(20);
    expect(component.positionedIndividuals[0][1].size).toBe(21.0);
    expect(component.positionedIndividuals[0][1].scaleFactor).toBe(1.0);
    expect(component.positionedIndividuals[0][1].xUpperLeftCorner).toBe(38.5);
    expect(component.positionedIndividuals[0][1].yUpperLeftCorner).toBe(9.5);

    expect(component.positionedIndividuals[1].length).toBe(1);
    expect(component.positionedIndividuals[1][0].individual.matingUnits.length).toBe(0);
    expect(component.positionedIndividuals[1][0].individual.pedigreeData.id).toBe('prb2');
    expect(component.positionedIndividuals[1][0].individual.parents.father.pedigreeData.id).toBe('dad2');
    expect(component.positionedIndividuals[1][0].individual.parents.mother.pedigreeData.id).toBe('mom2');
    expect(component.positionedIndividuals[1][0].individual.rank).toBe(1);
    expect(component.positionedIndividuals[1][0].xCenter).toBe(34.5);
    expect(component.positionedIndividuals[1][0].yCenter).toBe(50);
    expect(component.positionedIndividuals[1][0].size).toBe(21.0);
    expect(component.positionedIndividuals[1][0].scaleFactor).toBe(1.0);
    expect(component.positionedIndividuals[1][0].xUpperLeftCorner).toBe(24);
    expect(component.positionedIndividuals[1][0].yUpperLeftCorner).toBe(39.5);

    expect(component.lines.length).toBe(3);

    expect(component.lines[0].startX).toBe(20);
    expect(component.lines[0].startY).toBe(20);
    expect(component.lines[0].endX).toBe(49);
    expect(component.lines[0].endY).toBe(20);
    expect(component.lines[0].curved).toBe(false);
    expect(component.lines[0].curvedBaseHeight).toBeNaN();

    expect(component.lines[1].startX).toBe(34.5);
    expect(component.lines[1].startY).toBe(20);
    expect(component.lines[1].endX).toBe(34.5);
    expect(component.lines[1].endY).toBe(35);
    expect(component.lines[1].curved).toBe(false);
    expect(component.lines[1].curvedBaseHeight).toBeNaN();

    expect(component.lines[2].startX).toBe(34.5);
    expect(component.lines[2].startY).toBe(50);
    expect(component.lines[2].endX).toBe(34.5);
    expect(component.lines[2].endY).toBe(35);
    expect(component.lines[2].curved).toBe(false);
    expect(component.lines[2].curvedBaseHeight).toBeNaN();

    expect(component.pedigreeDataWithLayout.length).toBe(3);
    expect(component.pedigreeDataWithLayout[0].individual.pedigreeData.id).toBe('mom2');
    expect(component.pedigreeDataWithLayout[1].individual.pedigreeData.id).toBe('dad2');
    expect(component.pedigreeDataWithLayout[2].individual.pedigreeData.id).toBe('prb2');

    expect(component.width).toBe(60.5);
    expect(component.height).toBe(61.5);
  });

});
