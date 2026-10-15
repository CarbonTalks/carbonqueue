// Maps cq-sim live queue records (served by the backend at /queue/live) to queue rows.

export const TECH = {
  solar: { label: 'Solar PV', icon: 'wb_sunny' },
  onshore_wind: { label: 'Onshore wind', icon: 'air' },
  storage: { label: 'Battery storage', icon: 'battery_charging_full' },
  bioenergy_waste: { label: 'Bioenergy / waste', icon: 'compost' },
  other_renewable: { label: 'Other renewable', icon: 'water_drop' },
};

// Policies available in the live snapshot. Index order is used by settings and policy tabs.
export const LIVE_POLICIES = [
  { key: 'fifo', label: 'FIFO' },
  { key: 'carbon', label: 'Carbon only' },
  { key: 'carbonqueue', label: 'CarbonQueue' },
];

export const LANE_LABELS = {
  max_wait: 'Maximum-wait protection',
  small_quota: 'Small-project quota',
  carbon: 'Carbon impact / reviewer hour',
  unscored: 'Unscored lane',
  fifo: 'Submission order',
};

export function toRow(record) {
  const tech = TECH[record.category] || { label: record.technology || record.category, icon: 'bolt' };
  const band = record.daily_tco2;
  return {
    id: record.app_id,
    applicationId: record.application_id,
    name: record.site_name,
    authority: record.authority || '—',
    category: record.category,
    technology: record.technology,
    tech: tech.label,
    icon: tech.icon,
    capacity: record.generation_mw ?? 0,
    hasStorage: Boolean(record.has_storage),
    carbon: band ? [band.low, band.central, band.high] : null,
    risk: Math.round((record.p_withdraw_12m ?? 0) * 1000) / 10,
    effort: record.effort_hours,
    wait: record.wait_days,
    submitted: record.submitted,
    reason: record.reason,
    lane: record.lane,
    position: record.position || {},
    plannedWeek: record.planned_week || {},
  };
}

export const fmt = (value, digits = 1) =>
  value == null || Number.isNaN(value) ? '—' : Number(value).toLocaleString('en-GB', { maximumFractionDigits: digits, minimumFractionDigits: 0 });

// The live snapshot's lane and reason come from the CarbonQueue run; other policies get a matching plain reason.
export function reasonFor(p, policyKey) {
  if (policyKey === 'carbonqueue') return { lane: p.lane, text: p.reason };
  if (policyKey === 'fifo') return { lane: 'fifo', text: 'Submission order' };
  return p.carbon
    ? { lane: 'carbon', text: `Carbon impact: ${fmt(p.carbon[1], p.carbon[1] < 1 ? 2 : 1)} tCO₂e/day` }
    : { lane: 'unscored', text: 'Unscored lane: submission order' };
}
