import { UrlSerializer, UrlTree, DefaultUrlSerializer } from '@angular/router';

export class CustomUrlSerializer implements UrlSerializer {
  private defaultSerializer = new DefaultUrlSerializer();

  public parse(url: string): UrlTree {
    if (/\/{2,}/g.test(url)) {
      url = url.replace(/\/{2,}/g, '/');
    }
    return this.defaultSerializer.parse(url);
  }

  public serialize(tree: UrlTree): string {
    return this.defaultSerializer.serialize(tree);
  }
}
