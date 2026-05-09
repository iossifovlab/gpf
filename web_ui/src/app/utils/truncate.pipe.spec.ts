import { TruncatePipe } from './truncate.pipe';

describe('TruncatePipe', () => {
  it('should create an instance', () => {
    const pipe = new TruncatePipe();
    expect(pipe).toBeTruthy();
  });

  it('should truncate strings', () => {
    const pipe = new TruncatePipe();

    expect(pipe.transform('abcdefg', 3)).toBe('abc...');
    expect(pipe.transform('abcdefg', 5)).toBe('abcde...');
    expect(pipe.transform('abcdefg', 3, '/')).toBe('abc/');
    expect(pipe.transform('abcdefg', 7)).toBe('abcdefg');
  });
});
