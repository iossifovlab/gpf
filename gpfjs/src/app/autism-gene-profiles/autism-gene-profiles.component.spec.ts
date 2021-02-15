import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { AutismGeneToolConfig } from './autism-gene-profile';

import { AutismGeneProfilesComponent } from './autism-gene-profiles.component';

describe('AutismGeneProfilesComponent', () => {
  let component: AutismGeneProfilesComponent;
  let fixture: ComponentFixture<AutismGeneProfilesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AutismGeneProfilesComponent ],
      providers: [ConfigService],
      imports: [HttpClientTestingModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AutismGeneProfilesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get genes on initialization', () => {
    const getGenesSpy = spyOn(component['autismGeneProfilesService'], 'getGenes')
      .and.returnValue('fakeGenesObservable' as any);

    component.ngOnInit();
    expect((component['genes$'])).toEqual('fakeGenesObservable' as any);
  });

  it('should set table header data if config is passed', () => {
    expect(component.config).toEqual(undefined);

    component.config = new AutismGeneToolConfig(
      ['fakeAutismScore'],
      undefined,
      ['fakeGeneList'],
      undefined,
      ['fakeProtectionScore']
    );

    component.ngOnChanges();

    expect(component['shownGeneLists']).toEqual(['fakeGeneList']);
    expect(component['shownAutismScores']).toEqual(['fakeAutismScore']);
    expect(component['shownProtectionScores']).toEqual(['fakeProtectionScore']);
  });

  it('should calculate dataset colspan', () => {
    let mockDatasetConfig;

    mockDatasetConfig = {effects: [1, 2], personSets: [1, 2]};
    expect(component.calculateDatasetColspan(mockDatasetConfig)).toBe(4);

    mockDatasetConfig = {effects: [1, 2, 3], personSets: [1, 2]};
    expect(component.calculateDatasetColspan(mockDatasetConfig)).toBe(6);

    mockDatasetConfig = {effects: [1, 2, 3, 4], personSets: [1, 2, 3, 4, 6, 7]};
    expect(component.calculateDatasetColspan(mockDatasetConfig)).toBe(24);

    mockDatasetConfig = {effects: [1, 2, 3, 4, 5], personSets: [1, 2, 3, 4, 6, 7, 8]};
    expect(component.calculateDatasetColspan(mockDatasetConfig)).toBe(35);
  });
});
