// Reminder scheduling (synthetic example).
// Implements AIOPS-SW-003: reminder 23-25 hours before start.
export function reminderTime(start: Date): Date {
  return new Date(start.getTime() - 24 * 3600 * 1000);
}
