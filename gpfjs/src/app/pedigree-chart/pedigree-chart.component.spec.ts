import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { ChangeDetectorRef } from '@angular/core';

import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { PedigreeChartComponent } from './pedigree-chart.component';
import { PedigreeChartMemberComponent } from './pedigree-chart-member.component';
import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';
import { PerfectlyDrawablePedigreeService } from 'app/perfectly-drawable-pedigree/perfectly-drawable-pedigree.service';
import { ResizeService } from 'app/table/resize.service';

const FAMILY = [
  new PedigreeData('f1', 'prb1', 'dad1', 'mom1', 'M', 'prb',
                   'E35252', [75, 100], false, 'label', 'sl'),
  new PedigreeData('f1', 'dad1', '', '', 'M', 'dad', 'E0E0E0',
                   [50, 50], true, 'label', 'sl'),
  new PedigreeData('f1', 'mom1', '', '', 'F', 'mom', 'FFFFFF',
                   [100, 50], false, 'label', 'sl')
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

    component.family = FAMILY;

    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('should create lines', () => {
    expect(component.straightLines.length).toBe(3);
    expect(component.curveLines.length).toBe(0);
  });

  it('should scale svg', () => {
    component.scaleSvg();
    expect(component.scale).toBe(1);
    expect(component.getScaleString()).toBe('scale(1)');
  });

  it('should toggle maximized', () => {
    expect(component.maximized).toBe(false);
    component.toggleMaximize();
    expect(component.maximized).toBe(true);
    component.toggleMaximize();
    expect(component.maximized).toBe(false);
  });

  it('should return view box', () => {
    expect(component.getViewBox()).toBe('-8 0 81 81');
  });
});
