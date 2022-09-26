import { CustomUrlSerializer } from './custom-url-serializer';

describe('CustomUrlSerializer', () => {
  it('should trim any repeating slashes anywhere in the URL', () => {
    const cus = new CustomUrlSerializer();
    expect(
      cus.serialize(cus.parse('/bla1//bla2///////bla3////////////bla4//bla5/bla6'))
    ).toEqual('/bla1/bla2/bla3/bla4/bla5/bla6');
  });
});
