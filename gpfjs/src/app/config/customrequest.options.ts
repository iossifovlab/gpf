import { Injectable } from '@angular/core';
import { BaseRequestOptions, RequestOptions, RequestOptionsArgs } from '@angular/http';
import {Location} from '@angular/common';

import { ConfigService } from './config.service';

@Injectable()
export class CustomRequestOptions extends BaseRequestOptions {

  constructor(
    private configService: ConfigService
  ) {
    super();
  }

  merge(options?: RequestOptionsArgs): CustomRequestOptions {
    if (options.url) options.url = Location.joinWithSlash(this.configService.baseUrl, options.url);
    let result = <CustomRequestOptions> super.merge(options);
    result.merge = this.merge;
    result.configService = this.configService;
    return result
  }
}
