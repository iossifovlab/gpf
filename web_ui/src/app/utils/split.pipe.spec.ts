import { SplitPipe } from './split.pipe';

describe('SplitPipe', () => {
  it('should create an instance', () => {
    const pipe = new SplitPipe();
    expect(pipe).toBeTruthy();
  });

  it('should split strings', () => {
    const pipe = new SplitPipe();

    expect(pipe.transform('abc.de.f', '.')).toStrictEqual(['abc', 'de', 'f']);
    expect(pipe.transform('abc/def/g', '/')).toStrictEqual(['abc', 'def', 'g']);
    expect(pipe.transform('abcdbef', 'b')).toStrictEqual(['a', 'cd', 'ef']);
  });
});
