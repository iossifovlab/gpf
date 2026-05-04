/* eslint-disable @stylistic/max-len */
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ChangeDetectorRef } from '@angular/core';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { PedigreeChartComponent } from './pedigree-chart.component';
import { PedigreeChartMemberComponent } from './pedigree-chart-member.component';
import { PedigreeData } from 'app/genotype-preview-model/genotype-preview';
import { PerfectlyDrawablePedigreeService } from 'app/perfectly-drawable-pedigree/perfectly-drawable-pedigree.service';
import { ResizeService } from 'app/table/resize.service';
import { VariantReportsService } from 'app/variant-reports/variant-reports.service';
import { HttpClient, HttpHandler } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersService } from 'app/users/users.service';
import { APP_BASE_HREF } from '@angular/common';
import { RouterTestingModule } from '@angular/router/testing';
import { Observable } from 'rxjs/internal/Observable';
import { of } from 'rxjs';
import { StoreModule } from '@ngrx/store';

const mockFamilies = {
  familiesWithoutPosition: {
    f1: [
      new PedigreeData('f2', 'prb2', 'mom2', 'dad2', 'M', 'prb', '#E35252', null, false, 'label', 'sl'),
      new PedigreeData('f2', 'dad2', '', '', 'M', 'dad', '#E0E0E0', null, true, 'label', 'sl'),
      new PedigreeData('f2', 'mom2', '', '', 'F', 'mom', '#FFFFFF', null, false, 'label', 'sl')
    ],
    f2: [
      new PedigreeData('f', 'prb', 'mom', 'dad', 'M', 'prb', '#E35252', null, false, 'label', 'sl'),
      new PedigreeData('f', 'sib3', 'mom', 'dad', 'F', 'sib', '#FFFFFF', null, false, 'label', 'sl'),
      new PedigreeData('f', 'dad', '', '', 'M', 'dad', '#E0E0E0', null, false, 'label', 'sl'),
      new PedigreeData('f', 'mom', '', '', 'F', 'mom', '#FFFFFF', null, false, 'label', 'sl')
    ],
    f3: [
      // 3 columns pedigree
      new PedigreeData('f', 'prb', 'mom', 'dad', 'M', 'prb', '#E35252', null, false, 'label', 'sl'),
      new PedigreeData('f', 'sib4', 'mom', 'dad', 'F', 'sib', '#FFFFFF', null, false, 'label', 'sl'),
      new PedigreeData('f', 'dad', 'grandmom', 'grandad', 'M', 'dad', '#E0E0E0', null, false, 'label', 'sl'),
      new PedigreeData('f', 'mom', 'grandmom', 'grandad', 'F', 'mom', '#FFFFFF', null, false, 'label', 'sl'),
      new PedigreeData('f', 'grandad', '', '', 'M', 'dad', '#FFFFFF', null, false, 'label', 'sl'),
      new PedigreeData('f', 'grandmom', '', '', 'F', 'mom', '#FFFFFF', null, false, 'label', 'sl')
    ],
    f4: [
      // curved pedigree
      new PedigreeData('f', 'prb', 'mom', 'dad', 'M', 'prb', '#E35252', null, false, 'label', 'sl'),
      new PedigreeData('f', 'mom', '', '', 'F', 'mom', '#FFFFFF', null, false, 'label', 'sl'),
      new PedigreeData('f', 'dad', '', '', 'M', 'dad', '#E0E0E0', null, false, 'label', 'sl'),
      new PedigreeData('f', 'step_dad', '', '', 'M', 'step_dad', '#E0E0E0', null, false, 'label', 'sl'),
      new PedigreeData('f', 'maternal_half_sibling', '', '', 'F', 'maternal_half_sibling', '#E0E0E0', null, false, 'label', 'sl'),
      new PedigreeData('f', 'step_dad_2', '', '', 'M', 'step_dad', '#E0E0E0', null, false, 'label', 'sl'),
      new PedigreeData('f', 'maternal_half_sibling', '', '', 'M', 'maternal_half_sibling', '#E0E0E0', null, false, 'label', 'sl')
    ],
    f5: [
      new PedigreeData('f', '1', '0', '0', 'U', 'prb', '#205c85', null, false, '', '')
    ]
  },
  familiesWithPositions: {
    f1: [
      new PedigreeData('f1', 'prb1', 'mom1', 'dad1', 'M', 'prb', '#E35252', [75, 100], false, 'label', 'sl'),
      new PedigreeData('f1', 'dad1', '', '', 'M', 'dad', '#E0E0E0', [50, 50], true, 'label', 'sl'),
      new PedigreeData('f1', 'mom1', '', '', 'F', 'mom', '#FFFFFF', [100, 50], false, 'label', 'sl')
    ],
    f2: [
      // curved pedigree
      new PedigreeData('f', '1', '0', '0', 'M', 'dad', '#ffffff', [10, 50], false, '', ''),
      new PedigreeData('f', '2', '0', '0', 'F', 'mom', '#ffffff', [39, 50], false, '', ''),
      new PedigreeData('f', '3', '0', '0', 'M', 'step_dad', '#ffffff', [126, 50], false, '', ''),
      new PedigreeData('f', '4', '0', '0', 'M', 'step_dad', '#ffffff', [263.15625, 50], false, '', ''),
      new PedigreeData('f', '5', '2', '3', 'M', 'maternal_half_sibling', '#ffffff', [97, 80], false, '', ''),
      new PedigreeData('f', '6', '2', '3', 'F', 'maternal_half_sibling', '#ffffff', [68, 80], false, '', ''),
      new PedigreeData('f', '7', '2', '4', 'F', 'maternal_half_sibling', '#ffffff', [151.078125, 80], false, '', ''),
      new PedigreeData('f', '8', '2', '1', 'M', 'prb', '#e35252', [39, 80], false, '', ''),
      new PedigreeData('f', '9', '2', '1', 'M', 'sib', '#e35252', [10, 80], false, '', '')
    ],
    f3: [
      // huge pedigree with curve not on top
      new PedigreeData('f', '1', '0', '0', 'M', 'unknown', '#70513b', [94.12003523111343, 50], false, '', ''),
      new PedigreeData('f', '2', '0', '0', 'F', 'unknown', '#70513b', [193.8303743004799, 50], false, '', ''),
      new PedigreeData('f', '3', '0', '0', 'M', 'unknown', '#70513b', [319.4519726913509, 80], false, '', ''),
      new PedigreeData('f', '4', '2', '1', 'F', 'unknown', '#70513b', [237.2496002316475, 80], false, '', ''),
      new PedigreeData('f', '5', '2', '1', 'M', 'unknown', '#70513b', [50.70080929994583, 80], false, '', ''),
      new PedigreeData('f', '6', '0', '0', 'F', 'unknown', '#70513b', [208.2496002316475, 80], false, '', ''),
      new PedigreeData('f', '7', '4', '3', 'F', 'maternal_grandmother', '#d76060', [278.3507864614992, 110], false, '', ''),
      new PedigreeData('f', '8', '0', '0', 'M', 'maternal_grandfather', '#d76060', [356.88566023111343, 110], false, '', ''),
      new PedigreeData('f', '9', '0', '0', 'M', 'unknown', '#70513b', [250.20226894982625, 110], false, '', ''),
      new PedigreeData('f', '10', '6', '5', 'F', 'unknown', '#70513b', [143.97520476579666, 110], false, '', ''),
      new PedigreeData('f', '11', '0', '0', 'M', 'unknown', '#70513b', [86.34722477197647, 110], false, '', ''),
      new PedigreeData('f', '12', '6', '5', 'F', 'unknown', '#70513b', [114.97520476579666, 110], false, '', ''),
      new PedigreeData('f', '13', '0', '0', 'M', 'step_dad', '#e8c55a', [394.08878523111343, 140], false, '', ''),
      new PedigreeData('f', '14', '7', '8', 'F', 'mom', '#eb4c4c', [317.6182233463063, 140], false, '', ''),
      new PedigreeData('f', '15', '0', '0', 'M', 'dad', '#eb4c4c', [279.65128523111343, 140], false, '', ''),
      new PedigreeData('f', '16', '0', '0', 'M', 'step_dad', '#e8c55a', [519.9452343583107, 140], false, '', ''),
      new PedigreeData('f', '17', '0', '0', 'M', 'unknown', '#70513b', [144.83878523111343, 140], false, '', ''),
      new PedigreeData('f', '18', '10', '9', 'F', 'unknown', '#70513b', [182.58873685781145, 140], false, '', ''),
      new PedigreeData('f', '19', '10', '9', 'M', 'unknown', '#70513b', [211.58873685781145, 140], false, '', ''),
      new PedigreeData('f', '20', '0', '0', 'M', 'unknown', '#70513b', [30.338785231113434, 140], false, '', ''),
      new PedigreeData('f', '21', '12', '11', 'F', 'unknown', '#70513b', [100.66121476888657, 140], false, '', ''),
      new PedigreeData('f', '22', '14', '13', 'M', 'maternal_half_sibling', '#d76060', [355.85350428870987, 170], false, '', ''),
      new PedigreeData('f', '23', '14', '15', 'F', 'sib', '#eb4c4c', [298.63475428870987, 170], false, '', ''),
      new PedigreeData('f', '24', '14', '15', 'M', 'prb', '#ff3838', [327.63475428870987, 170], false, '', ''),
      new PedigreeData('f', '25', '14', '15', 'M', 'sib', '#eb4c4c', [269.63475428870987, 170], false, '', ''),
      new PedigreeData('f', '26', '14', '16', 'M', 'maternal_half_sibling', '#d76060', [418.7817288523085, 170], false, '', ''),
      new PedigreeData('f', '27', '18', '17', 'M', 'unknown', '#70513b', [178.21376104446244, 170], false, '', ''),
      new PedigreeData('f', '28', '18', '17', 'M', 'unknown', '#70513b', [149.21376104446244, 170], false, '', ''),
      new PedigreeData('f', '29', '21', '20', 'F', 'unknown', '#70513b', [47, 170], false, '', ''),
      new PedigreeData('f', '30', '21', '20', 'F', 'unknown', '#70513b', [121, 170], false, '', ''),
      new PedigreeData('f', '31', '21', '20', 'M', 'unknown', '#70513b', [84, 170], false, '', ''),
      new PedigreeData('f', '32', '21', '20', 'M', 'unknown', '#70513b', [10, 170], false, '', '')
    ],
    f4: [
      // 3 rows pedigree
      new PedigreeData('f', '1', '0', '0', 'F', 'mom', '#ffffff', [20.875, 50], false, '', ''),
      new PedigreeData('f', '2', '0', '0', 'M', 'dad', '#ffffff', [115.125, 50], false, '', ''),
      new PedigreeData('f', '3', '1', '2', 'M', 'prb', '#ff2121', [68, 80], false, '', ''),
      new PedigreeData('f', '4', '1', '2', 'M', 'sib', '#ffffff', [39, 80], false, '', ''),
      new PedigreeData('f', '5', '0', '0', 'F', 'unknown', '#ffffff', [10, 80], false, '', ''),
      new PedigreeData('f', '6', '1', '2', 'M', 'sib', '#ffffff', [97, 80], false, '', ''),
      new PedigreeData('f', '7', '5', '4', 'M', 'unknown', '#ff2121', [39, 110], false, '', ''),
      new PedigreeData('f', '8', '5', '4', 'F', 'unknown', '#ffffff', [10, 110], false, '', '')
    ],
    f5: [
      // wide pedigree
      new PedigreeData('f', '1', '0', '0', 'M', 'dad', '#ffffff', [39, 50], false, '', ''),
      new PedigreeData('f', '2', '0', '0', 'F', 'mom', '#ffffff', [82.5, 50], false, '', ''),
      new PedigreeData('f', '3', '0', '0', 'M', 'step_dad', '#ffffff', [124.1875, 50], false, '', ''),
      new PedigreeData('f', '5', '0', '0', 'F', 'step_mom', '#ffffff', [10, 50], false, '', ''),
      new PedigreeData('f', '6', '0', '0', 'F', 'unknown', '#ffffff', [228.78125, 50], false, '', ''),
      new PedigreeData('f', '7', '2', '1', 'M', 'prb', '#ff2121', [60.75, 80], false, '', ''),
      new PedigreeData('f', '8', '2', '3', 'M', 'maternal_half_sibling', '#ff2121', [117.84375, 80], false, '', ''),
      new PedigreeData('f', '9', '2', '3', 'F', 'maternal_half_sibling', '#ffffff', [88.84375, 80], false, '', ''),
      new PedigreeData('f', '10', '6', '3', 'M', 'unknown', '#ffffff', [176.484375, 80], false, '', ''),
      new PedigreeData('f', '11', '6', '3', 'M', 'unknown', '#ffffff', [147.484375, 80], false, '', ''),
      new PedigreeData('f', '12', '6', '3', 'M', 'unknown', '#ffffff', [205.484375, 80], false, '', ''),
      new PedigreeData('f', '13', '5', '1', 'F', 'paternal_half_sibling', '#ffffff', [24.5, 80], false, '', '')
    ],
    f6: [
      // 3 curve pedigree
      new PedigreeData('f', '1', '0', '0', 'M', 'dad', '#ffffff', [340, 50], false, '', ''),
      new PedigreeData('f', '2', '0', '0', 'F', 'mom', '#ffffff', [10, 50], false, '', ''),
      new PedigreeData('f', '3', '0', '0', 'M', 'step_dad', '#ffffff', [61, 50], false, '', ''),
      new PedigreeData('f', '4', '0', '0', 'F', 'step_mom', '#ffffff', [369, 50], false, '', ''),
      new PedigreeData('f', '5', '0', '0', 'M', 'step_dad', '#ffffff', [154, 50], false, '', ''),
      new PedigreeData('f', '6', '0', '0', 'F', 'step_mom', '#ffffff', [454, 50], false, '', ''),
      new PedigreeData('f', '7', '4', '1', 'M', 'paternal_half_sibling', '#ffffff', [354.5, 80], false, '', ''),
      new PedigreeData('f', '8', '6', '1', 'M', 'paternal_half_sibling', '#ffffff', [411.5, 80], false, '', ''),
      new PedigreeData('f', '9', '6', '1', 'M', 'paternal_half_sibling', '#ffffff', [382.5, 80], false, '', ''),
      new PedigreeData('f', '10', '2', '5', 'M', 'maternal_half_sibling', '#ffffff', [82, 80], false, '', ''),
      new PedigreeData('f', '11', '2', '3', 'F', 'maternal_half_sibling', '#ffffff', [54, 80], false, '', ''),
      new PedigreeData('f', '12', '2', '3', 'F', 'maternal_half_sibling', '#ffffff', [17, 80], false, '', ''),
      new PedigreeData('f', '13', '2', '1', 'F', 'prb', '#ff2121', [156.5, 80], false, '', ''),
      new PedigreeData('f', '14', '2', '1', 'M', 'sib', '#ff2121', [193.5, 80], false, '', '')
    ],
    f7: [
      new PedigreeData('f', '1', '8', '9', 'F', 'mom', '#ffffff', [328.578125, 110], false, '', ''),
      new PedigreeData('f', '2', '0', '0', 'M', 'dad', '#ffffff', [445.1929931640625, 110], false, '', ''),
      new PedigreeData('f', '3', '1', '2', 'M', 'sib', '#ffffff', [386.88555908203125, 140], false, '', ''),
      new PedigreeData('f', '4', '1', '2', 'M', 'prb', '#e35252', [415.88555908203125, 140], false, '', ''),
      new PedigreeData('f', '5', '1', '2', 'M', 'sib', '#e35252', [357.88555908203125, 140], false, '', ''),
      new PedigreeData('f', '6', '0', '0', 'F', 'unknown', '#ffffff', [277.595703125, 50], false, '', ''),
      new PedigreeData('f', '7', '0', '0', 'M', 'unknown', '#ffffff', [211.720703125, 50], false, '', ''),
      new PedigreeData('f', '8', '0', '0', 'F', 'maternal_grandmother', '#ffffff', [397.998046875, 80], false, '', ''),
      new PedigreeData('f', '9', '6', '7', 'M', 'maternal_grandfather', '#ffffff', [259.158203125, 80], false, '', ''),
      new PedigreeData('f', '10', '6', '7', 'M', 'unknown', '#ffffff', [230.158203125, 80], false, '', ''),
      new PedigreeData('f', '11', '0', '0', 'F', 'unknown', '#ffffff', [28.099609375, 80], false, '', ''),
      new PedigreeData('f', '12', '0', '0', 'M', 'unknown', '#ffffff', [300.470703125, 110], false, '', ''),
      new PedigreeData('f', '13', '11', '10', 'F', 'unknown', '#ffffff', [248.2578125, 110], false, '', ''),
      new PedigreeData('f', '14', '0', '0', 'M', 'unknown', '#ffffff', [84, 110], false, '', ''),
      new PedigreeData('f', '15', '11', '10', 'M', 'unknown', '#ffffff', [47, 110], false, '', ''),
      new PedigreeData('f', '16', '11', '10', 'F', 'unknown', '#ffffff', [10, 110], false, '', ''),
      new PedigreeData('f', '17', '13', '12', 'M', 'unknown', '#ffffff', [255.8642578125, 140], false, '', ''),
      new PedigreeData('f', '18', '13', '12', 'F', 'unknown', '#ffffff', [218.8642578125, 140], false, '', ''),
      new PedigreeData('f', '19', '13', '12', 'M', 'unknown', '#e35252', [329.8642578125, 140], false, '', ''),
      new PedigreeData('f', '20', '13', '12', 'M', 'unknown', '#ffffff', [292.8642578125, 140], false, '', ''),
      new PedigreeData('f', '21', '13', '14', 'M', 'unknown', '#e35252', [184.62890625, 140], false, '', ''),
      new PedigreeData('f', '22', '13', '14', 'F', 'unknown', '#ffffff', [147.62890625, 140], false, '', '')
    ],
    f8: [
      new PedigreeData('f', '1', '0', '0', 'M', 'unknown', '#ffffff', [153.75, 50], false, '', ''),
      new PedigreeData('f', '2', '0', '0', 'F', 'unknown', '#ffffff', [75.75, 50], false, '', ''),
      new PedigreeData('f', '3', '0', '0', 'F', 'unknown', '#ffffff', [211.75, 80], false, '', ''),
      new PedigreeData('f', '4', '2', '1', 'M', 'unknown', '#ffffff', [133.25, 80], false, '', ''),
      new PedigreeData('f', '5', '2', '1', 'F', 'unknown', '#ffffff', [96.25, 80], false, '', ''),
      new PedigreeData('f', '6', '0', '0', 'M', 'unknown', '#ffffff', [34.75, 80], false, '', ''),
      new PedigreeData('f', '7', '0', '0', 'M', 'maternal_grandfather', '#ffffff', [243.625, 110], false, '', ''),
      new PedigreeData('f', '8', '0', '0', 'F', 'maternal_grandmother', '#ffffff', [275.5, 110], false, '', ''),
      new PedigreeData('f', '9', '0', '0', 'M', 'paternal_grandfather', '#ffffff', [209.5, 110], false, '', ''),
      new PedigreeData('f', '10', '3', '4', 'F', 'paternal_grandmother', '#ffffff', [172.5, 110], false, '', ''),
      new PedigreeData('f', '11', '5', '6', 'F', 'unknown', '#ffffff', [65.5, 110], false, '', ''),
      new PedigreeData('f', '12', '0', '0', 'M', 'unknown', '#ffffff', [28.5, 110], false, '', ''),
      new PedigreeData('f', '13', '8', '7', 'F', 'mom', '#ffffff', [259.5625, 140], false, '', ''),
      new PedigreeData('f', '14', '10', '9', 'M', 'dad', '#ffffff', [191, 140], false, '', ''),
      new PedigreeData('f', '15', '11', '12', 'F', 'unknown', '#ffffff', [47, 140], false, '', ''),
      new PedigreeData('f', '16', '0', '0', 'M', 'unknown', '#ffffff', [10, 140], false, '', ''),
      new PedigreeData('f', '17', '13', '14', 'F', 'sib', '#ffffff', [239.78125, 170], false, '', ''),
      new PedigreeData('f', '18', '13', '14', 'M', 'prb', '#e35252', [210.78125, 170], false, '', ''),
      new PedigreeData('f', '19', '15', '16', 'F', 'unknown', '#ffffff', [43, 170], false, '', ''),
      new PedigreeData('f', '20', '15', '16', 'M', 'unknown', '#e35252', [14, 170], false, '', '')
    ]
  }
};

class MockDatasetsService {
  public getSelectedDataset(): object {
    return { id: 'testDataset' };
  }
}

class MockVariantReportsService {
  public getFamilies(): Observable<string[]> {
    return of(['family1', 'family2', 'family3']);
  }
}

describe('PedigreeChartComponent', () => {
  let component: PedigreeChartComponent;
  let fixture: ComponentFixture<PedigreeChartComponent>;
  const mockDatasetsService = new MockDatasetsService();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        PedigreeChartComponent,
        PedigreeChartMemberComponent
      ],
      imports: [
        NgbModule,
        RouterTestingModule,
        StoreModule.forRoot({})
      ],
      providers: [
        PerfectlyDrawablePedigreeService,
        ResizeService,
        ChangeDetectorRef,
        {provide: VariantReportsService, useValue: new MockVariantReportsService()},
        HttpClient,
        HttpHandler,
        ConfigService,
        {provide: DatasetsService, useValue: mockDatasetsService},
        UsersService,
        { provide: APP_BASE_HREF, useValue: '' }
      ]
    })
      .compileComponents();

    fixture = TestBed.createComponent(PedigreeChartComponent);
    component = fixture.componentInstance;
  }));

  it('should be created', () => {
    component.family = mockFamilies.familiesWithPositions.f1;
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should create lines', () => {
    component.family = mockFamilies.familiesWithPositions.f1;
    fixture.detectChanges();
    expect(component.straightLines).toHaveLength(3);
    expect(component.curveLines).toHaveLength(0);
  });

  it('should return the proper viewbox values for pedigrees WITHOUT positions', () => {
    component.family = mockFamilies.familiesWithoutPosition.f1;
    component.ngOnInit();
    expect(component.getViewBox()).toBe('-7.73 -7.88 66.95 68.25');

    component.family = mockFamilies.familiesWithoutPosition.f2;
    component.ngOnInit();
    expect(component.getViewBox()).toBe('-7.73 -7.88 66.95 68.25');

    component.family = mockFamilies.familiesWithoutPosition.f3;
    component.ngOnInit();
    expect(component.getViewBox()).toBe('-7.73 -12.38 66.95 107.25');

    component.family = mockFamilies.familiesWithoutPosition.f4;
    component.ngOnInit();
    expect(component.getViewBox()).toBe('-14.25 -12.38 123.5 107.25');

    component.family = mockFamilies.familiesWithoutPosition.f5;
    component.ngOnInit();
    expect(component.getViewBox()).toBe('-3.38 -3.38 29.25 35.25');
  });

  it('should return the proper viewbox values for pedigrees WITH positions', () => {
    component.family = mockFamilies.familiesWithPositions.f1;
    component.ngOnInit();
    expect(component.getViewBox()).toBe('-10.95 -10.95 94.9 94.9');

    component.family = mockFamilies.familiesWithPositions.f2;
    component.ngOnInit();
    expect(component.getViewBox()).toBe('-41.42 -19.95 359 80.9');

    component.family = mockFamilies.familiesWithPositions.f3;
    component.ngOnInit();
    expect(component.getViewBox()).toBe('-79.94 -21.45 692.83 185.9');

    component.family = mockFamilies.familiesWithPositions.f4;
    component.ngOnInit();
    expect(component.getViewBox()).toBe('-19.22 -12.45 166.56 107.9');

    component.family = mockFamilies.familiesWithPositions.f5;
    component.ngOnInit();
    expect(component.getViewBox()).toBe('-36.27 -7.95 314.32 68.9');

    component.family = mockFamilies.familiesWithPositions.f6;
    component.ngOnInit();
    expect(component.getViewBox()).toBe('-70.05 -19.95 607.1 80.9');

    component.family = mockFamilies.familiesWithPositions.f7;
    component.ngOnInit();
    expect(component.getViewBox()).toBe('-68.73 -16.95 595.65 146.9');

    component.family = mockFamilies.familiesWithPositions.f8;
    component.ngOnInit();
    expect(component.getViewBox()).toBe('-43.28 -21.45 375.05 185.9');
  });

  it('should load pedigree with positions', () => {
    component.family = mockFamilies.familiesWithPositions.f1;
    fixture.detectChanges();

    component.ngOnInit();

    expect(component.positionedIndividuals).toHaveLength(2);

    expect(component.positionedIndividuals[0]).toHaveLength(2);

    expect(component.positionedIndividuals[0][0].individual.matingUnits).toHaveLength(1);
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.individuals).toHaveLength(1);
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.individuals[0].pedigreeData.id).toBe('prb1');
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.toString()).toBe('s{prb1}');
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.individualSet().size).toBe(1);
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.childrenSet()).toStrictEqual(new Set());
    expect(component.positionedIndividuals[0][0].individual.pedigreeData.id).toBe('dad1');
    expect(component.positionedIndividuals[0][0].individual.parents).toBeUndefined();
    expect(component.positionedIndividuals[0][0].individual.rank).toBe(-3673473456);
    expect(component.positionedIndividuals[0][0].xCenter).toBe(11.5);
    expect(component.positionedIndividuals[0][0].yCenter).toBe(11.5);
    expect(component.positionedIndividuals[0][0].size).toBe(21.0);
    expect(component.positionedIndividuals[0][0].scaleFactor).toBe(1.0);
    expect(component.positionedIndividuals[0][0].xUpperLeftCorner).toBe(1);
    expect(component.positionedIndividuals[0][0].yUpperLeftCorner).toBe(1);

    expect(component.positionedIndividuals[0][1].individual.matingUnits).toHaveLength(1);
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.individuals).toHaveLength(1);
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.individuals[0].pedigreeData.id).toBe('prb1');
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.toString()).toBe('s{prb1}');
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.individualSet().size).toBe(1);
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.childrenSet()).toStrictEqual(new Set());
    expect(component.positionedIndividuals[0][1].individual.pedigreeData.id).toBe('mom1');
    expect(component.positionedIndividuals[0][1].individual.parents).toBeUndefined();
    expect(component.positionedIndividuals[0][1].individual.rank).toBe(-3673473456);
    expect(component.positionedIndividuals[0][1].xCenter).toBe(61.5);
    expect(component.positionedIndividuals[0][1].yCenter).toBe(11.5);
    expect(component.positionedIndividuals[0][1].size).toBe(21.0);
    expect(component.positionedIndividuals[0][1].scaleFactor).toBe(1.0);
    expect(component.positionedIndividuals[0][1].xUpperLeftCorner).toBe(51);
    expect(component.positionedIndividuals[0][1].yUpperLeftCorner).toBe(1);

    expect(component.positionedIndividuals[1]).toHaveLength(1);
    expect(component.positionedIndividuals[1][0].individual.matingUnits).toHaveLength(0);
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

    expect(component.lines).toHaveLength(3);

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

    expect(component.pedigreeDataWithLayout).toHaveLength(3);
    expect(component.pedigreeDataWithLayout[0].individual.pedigreeData.id).toBe('dad1');
    expect(component.pedigreeDataWithLayout[1].individual.pedigreeData.id).toBe('mom1');
    expect(component.pedigreeDataWithLayout[2].individual.pedigreeData.id).toBe('prb1');

    expect(component.width).toBe(73);
    expect(component.height).toBe(73);
  });

  it('should load pedigree without positions', () => {
    component.family = mockFamilies.familiesWithoutPosition.f1;

    component.ngOnInit();

    expect(component.positionedIndividuals).toHaveLength(2);

    expect(component.positionedIndividuals[0]).toHaveLength(2);
    expect(component.positionedIndividuals[0][0].individual.matingUnits).toHaveLength(1);
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.individuals).toHaveLength(1);
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.individuals[0].pedigreeData.id).toBe('prb2');
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.toString()).toBe('s{prb2}');
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.individualSet().size).toBe(1);
    expect(component.positionedIndividuals[0][0].individual.matingUnits[0].children.childrenSet()).toStrictEqual(new Set());
    expect(component.positionedIndividuals[0][0].individual.pedigreeData.id).toBe('mom2');
    expect(component.positionedIndividuals[0][0].individual.parents).toBeUndefined();
    expect(-component.positionedIndividuals[0][0].individual.rank).toBe(0);
    expect(component.positionedIndividuals[0][0].xCenter).toBe(11);
    expect(component.positionedIndividuals[0][0].yCenter).toBe(11);
    expect(component.positionedIndividuals[0][0].size).toBe(21.0);
    expect(component.positionedIndividuals[0][0].scaleFactor).toBe(1.0);
    expect(component.positionedIndividuals[0][0].xUpperLeftCorner).toBe(0.5);
    expect(component.positionedIndividuals[0][0].yUpperLeftCorner).toBe(0.5);

    expect(component.positionedIndividuals[0][1].individual.matingUnits).toHaveLength(1);
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.individuals).toHaveLength(1);
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.individuals[0].pedigreeData.id).toBe('prb2');
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.toString()).toBe('s{prb2}');
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.individualSet().size).toBe(1);
    expect(component.positionedIndividuals[0][1].individual.matingUnits[0].children.childrenSet()).toStrictEqual(new Set());
    expect(component.positionedIndividuals[0][1].individual.pedigreeData.id).toBe('dad2');
    expect(component.positionedIndividuals[0][1].individual.parents).toBeUndefined();
    expect(component.positionedIndividuals[0][1].individual.rank === 0).toBe(true);
    expect(component.positionedIndividuals[0][1].xCenter).toBe(40);
    expect(component.positionedIndividuals[0][1].yCenter).toBe(11);
    expect(component.positionedIndividuals[0][1].size).toBe(21.0);
    expect(component.positionedIndividuals[0][1].scaleFactor).toBe(1.0);
    expect(component.positionedIndividuals[0][1].xUpperLeftCorner).toBe(29.5);
    expect(component.positionedIndividuals[0][1].yUpperLeftCorner).toBe(0.5);

    expect(component.positionedIndividuals[1]).toHaveLength(1);
    expect(component.positionedIndividuals[1][0].individual.matingUnits).toHaveLength(0);
    expect(component.positionedIndividuals[1][0].individual.pedigreeData.id).toBe('prb2');
    expect(component.positionedIndividuals[1][0].individual.parents.father.pedigreeData.id).toBe('dad2');
    expect(component.positionedIndividuals[1][0].individual.parents.mother.pedigreeData.id).toBe('mom2');
    expect(component.positionedIndividuals[1][0].individual.rank).toBe(1);
    expect(component.positionedIndividuals[1][0].xCenter).toBe(25.5);
    expect(component.positionedIndividuals[1][0].yCenter).toBe(41);
    expect(component.positionedIndividuals[1][0].size).toBe(21.0);
    expect(component.positionedIndividuals[1][0].scaleFactor).toBe(1.0);
    expect(component.positionedIndividuals[1][0].xUpperLeftCorner).toBe(15);
    expect(component.positionedIndividuals[1][0].yUpperLeftCorner).toBe(30.5);

    expect(component.lines).toHaveLength(3);

    expect(component.lines[0].startX).toBe(11);
    expect(component.lines[0].startY).toBe(11);
    expect(component.lines[0].endX).toBe(40);
    expect(component.lines[0].endY).toBe(11);
    expect(component.lines[0].curved).toBe(false);
    expect(component.lines[0].curvedBaseHeight).toBeNaN();

    expect(component.lines[1].startX).toBe(25.5);
    expect(component.lines[1].startY).toBe(11);
    expect(component.lines[1].endX).toBe(25.5);
    expect(component.lines[1].endY).toBe(26);
    expect(component.lines[1].curved).toBe(false);
    expect(component.lines[1].curvedBaseHeight).toBeNaN();

    expect(component.lines[2].startX).toBe(25.5);
    expect(component.lines[2].startY).toBe(41);
    expect(component.lines[2].endX).toBe(25.5);
    expect(component.lines[2].endY).toBe(26);
    expect(component.lines[2].curved).toBe(false);
    expect(component.lines[2].curvedBaseHeight).toBeNaN();

    expect(component.pedigreeDataWithLayout).toHaveLength(3);
    expect(component.pedigreeDataWithLayout[0].individual.pedigreeData.id).toBe('mom2');
    expect(component.pedigreeDataWithLayout[1].individual.pedigreeData.id).toBe('dad2');
    expect(component.pedigreeDataWithLayout[2].individual.pedigreeData.id).toBe('prb2');

    expect(component.width).toBe(51.5);
    expect(component.height).toBe(52.5);
  });

  it('should not duplicate pedigree individuals on repeat ngOnInit calls', () => {
    component.family = mockFamilies.familiesWithoutPosition.f1;
    component.ngOnInit();
    expect(component.positionedIndividuals).toHaveLength(2);
    expect(component.lines).toHaveLength(3);
    expect(component.pedigreeDataWithLayout).toHaveLength(3);
    fixture.detectChanges();
    expect(component.positionedIndividuals).toHaveLength(2);
    expect(component.lines).toHaveLength(3);
    expect(component.pedigreeDataWithLayout).toHaveLength(3);
  });
});
