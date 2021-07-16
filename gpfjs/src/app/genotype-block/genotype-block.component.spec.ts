/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { GenotypeBlockComponent } from './genotype-block.component';
import { GenderComponent } from '../gender/gender.component';
import { VarianttypesComponent } from '../varianttypes/varianttypes.component';
import { EffecttypesComponent } from '../effecttypes/effecttypes.component';
import { PedigreeSelectorComponent } from '../pedigree-selector/pedigree-selector.component';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersService } from 'app/users/users.service';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ConfigService } from 'app/config/config.service';
import { RouterTestingModule } from '@angular/router/testing';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { EffecttypesColumnComponent } from 'app/effecttypes/effecttypes-column.component';
import { NgxsModule } from '@ngxs/store';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { EffecttypesState } from 'app/effecttypes/effecttypes.state';
import { GenderState } from 'app/gender/gender.state';
import { VarianttypesState } from 'app/varianttypes/varianttypes.state';

describe('GenotypeBlockComponent', () => {
  let component: GenotypeBlockComponent;
  let fixture: ComponentFixture<GenotypeBlockComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [
        GenderComponent,
        VarianttypesComponent,
        EffecttypesComponent,
        GenotypeBlockComponent,
        PedigreeSelectorComponent,
        ErrorsAlertComponent,
        EffecttypesComponent,
        EffecttypesColumnComponent
      ],
      providers: [
        DatasetsService,
        UsersService,
        ConfigService,
      ],
      imports: [
        NgbModule,
        HttpClientTestingModule,
        RouterTestingModule,
        NgxsModule.forRoot([EffecttypesState, GenderState, VarianttypesState])
      ],
      schemas: [
        NO_ERRORS_SCHEMA
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GenotypeBlockComponent);
    component = fixture.componentInstance;
    component.dataset = {'genotypeBrowserConfig': {
      'inheritanceTypeFilter': new Set(),
      'variantTypes': new Set(),
      'selectedVariantTypes': new Set(),
    } as any} as any;
    fixture.detectChanges();
  });

  it('should create', () =>   {
    expect(component).toBeTruthy();
  });
});
