/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { GenotypeBlockComponent } from './genotype-block.component';
import { GenderComponent } from '../gender/gender.component';
import { VarianttypesComponent } from '../varianttypes/varianttypes.component';
import { EffecttypesComponent } from '../effecttypes/effecttypes.component';
import { PedigreeSelectorComponent } from '../pedigree-selector/pedigree-selector.component';



describe('GenotypeBlockComponent', () => {
  let component: GenotypeBlockComponent;
  let fixture: ComponentFixture<GenotypeBlockComponent>;

  beforeEach(async(() => {
    const storeSpy = jasmine.createSpyObj('Store', ['dispatch', 'subscribe', 'select', 'let']);
    TestBed.configureTestingModule({
      declarations: [
        GenderComponent,
        VarianttypesComponent,
        EffecttypesComponent,
        GenotypeBlockComponent,
        PedigreeSelectorComponent,
      ],
      imports: [
        NgbModule.forRoot(),


      ],
      providers: [
      ]
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenotypeBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
