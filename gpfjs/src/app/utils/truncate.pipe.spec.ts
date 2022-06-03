import { TruncatePipe } from './truncate.pipe';

describe('TruncatePipe', () => {
  it('should create an instance', () => {
    const pipe = new TruncatePipe();
    expect(pipe).toBeTruthy();
  });

  it('should truncate strings', () => {
    const pipe = new TruncatePipe();

    expect(pipe.transform('abcdefg', 3)).toEqual('abc...');
    expect(pipe.transform('abcdefg', 5)).toEqual('abcde...');
    expect(pipe.transform('abcdefg', 3, '/')).toEqual('abc/');
    expect(pipe.transform('abcdefg', 7)).toEqual('abcdefg');
  });
});
