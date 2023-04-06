import { enableProdMode } from '@angular/core';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';
import { AppModule } from './app/app.module';
import { environment } from './environments/environment';
import * as Sentry from '@sentry/angular-ivy';

Sentry.init({
  dsn: 'https://0@0.ingest.sentry.io/0', // wdae/sentry/views.py
  tunnel: 'http://localhost:8000/api/v3/sentry/',
  tracesSampleRate: 1.0,
});

if (environment.production) {
  enableProdMode();
}

platformBrowserDynamic().bootstrapModule(AppModule).catch(err => console.log(err));
