import { reminderTime } from '../src/reminders';

// AIOPS-SW-003
test('reminder is sent 24 hours before start', () => {
  const start = new Date('2026-11-02T09:00:00Z');
  expect(reminderTime(start).toISOString()).toBe('2026-11-01T09:00:00.000Z');
});
