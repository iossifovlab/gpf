import { TestBed } from '@angular/core/testing';
import { BackgroundColorPipe } from './background-color.pipe';
import { PValueIntensityPipe } from './p-value-intensity.pipe';

describe('BackgroundColorPipe', () => {
  let pipe: BackgroundColorPipe;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [BackgroundColorPipe, PValueIntensityPipe]
    });
    pipe = TestBed.inject(BackgroundColorPipe);
  });

  it('should create an instance', () => {
    expect(pipe).toBeTruthy();
  });

  it('should get rgba background color', () => {
    expect(pipe.transform('0.525')).toBe('rgba(255, 255, 255, 0.8)');
    expect(pipe.transform('0.005')).toBe('rgba(255, 138, 138, 0.8)');
    expect(pipe.transform('0.0001')).toBe('rgba(255, 51, 51, 0.8)');
    expect(pipe.transform('0.02')).toBe('rgba(255, 168, 168, 0.8)');
  });
});
