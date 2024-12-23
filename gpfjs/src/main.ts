import { enableProdMode } from '@angular/core';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';
import { AppModule } from './app/app.module';
import { environment } from './environments/environment';
import * as Sentry from '@sentry/angular';

if (environment.production) {
  enableProdMode();

  Sentry.init({
    dsn: 'https://0@0.ingest.sentry.io/0', // wdae/sentry/views.py
    tunnel: environment.apiPath + environment.sentryTunnel,
    tracesSampleRate: 1.0,
    release: environment.version
  });
}

platformBrowserDynamic().bootstrapModule(AppModule).catch(err => console.log(err));
