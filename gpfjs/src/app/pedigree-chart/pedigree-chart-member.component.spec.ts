import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PedigreeChartMemberComponent } from './pedigree-chart-member.component';

describe('PedigreeChartMemberComponent', () => {
  let component: PedigreeChartMemberComponent;
  let fixture: ComponentFixture<PedigreeChartMemberComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PedigreeChartMemberComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PedigreeChartMemberComponent);
    component = fixture.componentInstance;
    component.pedigreeData = {
      pedigreeIdentifier: 'pi',
      id: 'id',
      father: 'dad',
      mother: 'mom',
      gender: 'M',
      role: 'prb',
      color: 'F0F0F0',
      position: [5, 10],
      generated: true,
      label: 'label',
      smallLabel: 'sl'
    };
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('should have pedigree data', () => {
    expect(component.pedigreeData.id).toBe('id');
  });
});
