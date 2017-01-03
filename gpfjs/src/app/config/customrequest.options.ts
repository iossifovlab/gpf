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

  merge(options?: RequestOptionsArgs): RequestOptions {
    options.url = Location.joinWithSlash(this.configService.baseUrl, options.url);
    return super.merge(options);
  }
}
