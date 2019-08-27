import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { of } from 'rxjs';

import { GenotypePreviewChromosomesComponent } from './genotype-preview-chromosomes.component';
import { ChromosomeComponent } from '../chromosome/chromosome.component';
import { ChromosomeService } from '../chromosome-service/chromosome.service';
import { Chromosome } from '../chromosome-service/chromosome';


class MockedChromosomeService {
  getChromosomes() {
    let sampleBands = [
      {start: 0, end: 100, name: 'p6', gieStain: 'gneg'},
      {start: 100, end: 200, name: 'p5', gieStain: 'gpos25'},
      {start: 200, end: 300, name: 'p4', gieStain: 'gpos50'},
      {start: 300, end: 400, name: 'p3', gieStain: 'gpos75'},
      {start: 400, end: 500, name: 'p2', gieStain: 'gpos100'},
      {start: 500, end: 600, name: 'p1', gieStain: 'acen'},
      {start: 600, end: 700, name: 'q1', gieStain: 'acen'},
      {start: 700, end: 900, name: 'q2', gieStain: 'gpos100'},
      {start: 900, end: 1100, name: 'q3', gieStain: 'gpos75'},
      {start: 1100, end: 1300, name: 'q4', gieStain: 'gpos50'},
      {start: 1300, end: 1500, name: 'q5', gieStain: 'gpos25'},
      {start: 1500, end: 1700, name: 'q6', gieStain: 'gneg'},
      {start: 1700, end: 1750, name: 'q7', gieStain: 'stalk'},
      {start: 1750, end: 1800, name: 'q8', gieStain: 'gvar'},
    ];

    let chromosomes = [];

    for (let i of Array.from(Array(24).keys())) {
      let chrName = i == 22 ? 'X' : i == 23 ? 'Y' : (i+1).toString();
      chromosomes.push(Chromosome.fromJson({ name: chrName, bands: sampleBands }));
    }
    return of(chromosomes);
  }
}


describe('GenotypePreviewChromosomesComponent', () => {
  let component: GenotypePreviewChromosomesComponent;
  let fixture: ComponentFixture<GenotypePreviewChromosomesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [ NgbModule ],
      declarations: [ GenotypePreviewChromosomesComponent, ChromosomeComponent ],
      providers: [
        GenotypePreviewChromosomesComponent,
        { provide: ChromosomeService, useClass: MockedChromosomeService }
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenotypePreviewChromosomesComponent);
    component = fixture.componentInstance;

    // add empty lists of variants to allow chromosomes to draw
    component.genotypePreviewsByChromosome = {};
    for (let i of Array.from(Array(24).keys())) {
      let chrName = i == 22 ? 'X' : i == 23 ? 'Y' : (i+1).toString();
      component.genotypePreviewsByChromosome[chrName] = [];
    }

    // set column width directly to allow chromosomes to draw without calling ngOnChanges
    component.leftColumnWidth = 300;
    component.rightColumnWidth = 300;

    component.ngOnInit();
    fixture.detectChanges();
  });

  it('should be created', () => {
    expect(component).toBeTruthy();
  });

  it('should render all chromosomes', () => {
    let chromElems = fixture.debugElement.queryAll((el) => el.nativeElement.tagName == 'GPF-CHROMOSOME');
    expect(chromElems.length).toEqual(24);
  });
});
