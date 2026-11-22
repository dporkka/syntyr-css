/* Cloudflare Pages Function; only this one route invokes server-side code. */
import {onCustomersRequest} from '../../../lib/htmx-demo.mjs';

export function onRequest({request}) {
  return onCustomersRequest(request);
}
