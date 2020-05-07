import { TestBed } from '@angular/core/testing';

import { GeneVisualizationService } from './gene-visualization.service';

describe('GeneVisualizationService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: GeneVisualizationService = TestBed.get(GeneVisualizationService);
    expect(service).toBeTruthy();
  });
});
