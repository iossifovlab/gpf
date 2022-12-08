import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { ConfigService } from 'app/config/config.service';
import { QueryService } from 'app/query/query.service';
import { RouterTestingModule } from '@angular/router/testing';
import { AutismGeneProfilesBlockComponent } from './autism-gene-profiles-block.component';
import { AgpTableComponent } from 'app/autism-gene-profiles-table/autism-gene-profiles-table.component';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersService } from 'app/users/users.service';
import { NgxsModule } from '@ngxs/store';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';
import { FormsModule } from '@angular/forms';
import { APP_BASE_HREF } from '@angular/common';

describe('AutismGeneProfilesBlockComponent', () => {
  let component: AutismGeneProfilesBlockComponent;
  let fixture: ComponentFixture<AutismGeneProfilesBlockComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [AutismGeneProfilesBlockComponent, AgpTableComponent, MultipleSelectMenuComponent],
      providers: [
        ConfigService, QueryService, DatasetsService, UsersService, { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [
        HttpClientTestingModule, NgbNavModule, RouterTestingModule, FormsModule,
        NgxsModule.forRoot([], {developmentMode: true})
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AutismGeneProfilesBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
