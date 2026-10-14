export const queueSortLabels = {
  name: 'Project & Developer', tech: 'Technology', capacity: 'Capacity',
  carbon: 'Est. Carbon Impact', risk: 'Withdrawal', effort: 'Effort',
  wait: 'Waiting', reason: 'Reason', compliant: 'Compliance',
};

export const queueReason = project => project.wait > 120
  ? 'Maximum-wait protection' : 'Carbon impact / reviewer hour';

export function compareQueueProjects(a, b, { key, direction }) {
  // Unspecified capacity stays last in both directions.
  if (key === 'capacity' && (!a.capacity || !b.capacity)) {
    return Number(!a.capacity) - Number(!b.capacity);
  }
  const value = project => key === 'carbon' ? project.carbon[0]
    : key === 'reason' ? queueReason(project)
    : key === 'compliant' ? (project.compliant ? 'Compliant' : 'Non-compliant')
    : project[key];
  const left = value(a), right = value(b);
  let comparison = typeof left === 'string' ? left.localeCompare(right) : left - right;
  if (!comparison && key === 'name') comparison = a.developer.localeCompare(b.developer);
  return comparison * (direction === 'desc' ? -1 : 1);
}
