// Standalone validation: the server must still authorize and persist real writes.
export function validateAccountName(entry) {
  if (typeof entry !== 'string') {
    return { value: '', error: 'Enter an account name.' };
  }
  const value = entry.trim();
  if (!value) return { value: '', error: 'Enter an account name.' };
  // HTML minlength/maxlength use UTF-16 units, not user-facing characters.
  // Count Unicode code points and never echo a split surrogate pair.
  const characters = Array.from(value);
  if (characters.length > 80) {
    return { value: characters.slice(0, 80).join(''), error: 'Use 80 characters or fewer.' };
  }
  if (characters.length < 2) {
    return { value, error: 'Use at least 2 characters.' };
  }
  return { value, error: null };
}
