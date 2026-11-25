import { fail } from '@sveltejs/kit';
import { validateAccountName } from '../../lib/validation.js';

// Deliberately side-effect free. Production endpoints must authorize, apply
// CSRF protections, persist data, and handle concurrent writes.
export const actions = {
  default: async ({ request }) => {
    let body;
    try {
      body = await request.formData();
    } catch (error) {
      // A syntactically malformed multipart/form body is a client error.
      // Do not mask unrelated failures outside this parsing boundary.
      if (!(error instanceof TypeError)) throw error;
      return fail(400, { value: '', errors: { name: 'Malformed form submission.' } });
    }
    const { value, error } = validateAccountName(body.get('name'));
    if (error) {
      return fail(400, { value, errors: { name: error } });
    }
    return { success: true, value };
  }
};
