import { SplitPipe } from './split.pipe';

describe('SplitPipe', () => {
  it('should create an instance', () => {
    const pipe = new SplitPipe();
    expect(pipe).toBeTruthy();
  });

  it('should split strings', () => {
    const pipe = new SplitPipe();

    expect(pipe.transform('abc.de.f', '.')).toEqual(['abc', 'de', 'f']);
    expect(pipe.transform('abc/def/g', '/')).toEqual(['abc', 'def', 'g']);
    expect(pipe.transform('abcdbef', 'b')).toEqual(['a', 'cd', 'ef']);
  });
});
