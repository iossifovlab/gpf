import { HttpResponse } from '@angular/common/http';

export function downloadBlobResponse(response: HttpResponse<Blob>, filename: string) {
  const downloadLink = document.createElement('a');
  const url = URL.createObjectURL(new Blob([response.body], { type: response.body.type }));
  downloadLink.href = url;
  downloadLink.download = filename;
  downloadLink.click();
  window.URL.revokeObjectURL(url);
}
