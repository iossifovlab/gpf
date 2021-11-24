/* eslint-disable no-unused-vars, @typescript-eslint/no-unused-vars */

import { TestBed, waitForAsync } from '@angular/core/testing';
import { AppComponent } from './app.component';
import { GenderComponent } from './gender/gender.component';
import { VariantTypesComponent } from './variant-types/variant-types.component';
import { DatasetsService } from './datasets/datasets.service';
import { DatasetsComponent } from './datasets/datasets.component';
// import { DatasetsServiceStub } from './datasets/datasets.service.spec';
import { EffectTypesComponent } from './effect-types/effect-types.component';
import { GenotypeBlockComponent } from './genotype-block/genotype-block.component';
import { RegionsBlockComponent } from './regions-block/regions-block.component';
import { GenesBlockComponent } from './genes-block/genes-block.component';
import { PedigreeSelectorComponent } from './pedigree-selector/pedigree-selector.component';


import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

/*
describe('AppComponent', () => {
  beforeEach(() => {
    const storeSpy = jasmine.createSpyObj('Store', ['dispatch', 'subscribe', 'select', 'let']);
    TestBed.configureTestingModule({
      declarations: [
        AppComponent,
        DatasetsComponent,
        GenderComponent,
        VariantTypesComponent,
        EffectTypesComponent,
        EffecttypesColumnComponent,
        GenotypeBlockComponent,
        RegionsBlockComponent,
        GenesBlockComponent,
        PedigreeSelectorComponent,
      ],
      imports: [
        NgbModule,

      ],
      providers: [
        {
          provide: DatasetsService,
          useValue: new DatasetsServiceStub()
        },
      ]
    });
    TestBed.compileComponents();
  });

  it('should create the app', async(() => {
    let fixture = TestBed.createComponent(AppComponent);
    let app = fixture.debugElement.componentInstance;
    expect(app).toBeTruthy();
  }));

  it(`should have as title 'GPF: Genotypes and Phenotypes in Families'`, async(() => {
    let fixture = TestBed.createComponent(AppComponent);
    let app = fixture.debugElement.componentInstance;
    expect(app.title).toEqual(app.title);
  }));

  it('should render title in a h3 tag', async(() => {
    let fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    let compiled = fixture.debugElement.nativeElement;
    let app = fixture.debugElement.componentInstance;
    expect(compiled.querySelector('h3').textContent).toContain(app.title);
  }));
});
*/
