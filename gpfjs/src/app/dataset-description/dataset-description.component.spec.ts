import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Component, OnInit } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersService } from 'app/users/users.service';
import { Observable, of } from 'rxjs';
import { DatasetDescriptionComponent } from './dataset-description.component';

@Component({
  selector: 'gpf-dataset-description',
  templateUrl: './dataset-description.component.html',
  styleUrls: ['./dataset-description.component.css']
})
export class MockDatasetDescriptionComponent extends DatasetDescriptionComponent {
  ngOnInit() {}
}

describe('DatasetDescriptionComponent', () => {
  let component: MockDatasetDescriptionComponent;
  let fixture: ComponentFixture<MockDatasetDescriptionComponent>;

  beforeEach(async(() => {

    TestBed.configureTestingModule({
      declarations: [MockDatasetDescriptionComponent],
      providers: [
        {provide: ActivatedRoute, useValue: new ActivatedRoute()},
        DatasetsService,
        UsersService,
        ConfigService,
      ],
      imports: [RouterTestingModule, HttpClientTestingModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MockDatasetDescriptionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
