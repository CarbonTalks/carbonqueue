// Illustrative weekly operations, independent of the historical simulation cohort.
export const weeks = [
  {label:'14–18 Sep 2026', received:[5,6,4,7,5], completed:[3,4,4,5,4], wait:[64,62,60,59,58], hours:[42,44,43,46,45]},
  {label:'21–25 Sep 2026', received:[6,5,7,5,6], completed:[4,5,4,5,5], wait:[59,58,57,56,55], hours:[44,46,45,48,47]},
  {label:'28 Sep–2 Oct 2026', received:[6,7,5,6,7], completed:[5,5,6,5,6], wait:[56,55,54,53,52], hours:[46,47,48,49,46]},
  {label:'5–9 Oct 2026', received:[7,6,8,6,7], completed:[6,7,6,7,6], wait:[53,52,51,50,49], hours:[48,46,50,47,47]},
];
export const days = ['Mon','Tue','Wed','Thu','Fri'];
export const sum = values => values.reduce((total,value)=>total+value,0);
export function summarize(week) {
  const completed=sum(week.completed), received=sum(week.received), hours=sum(week.hours);
  return {completed,received,hours,capacity:320,utilization:hours/320*100,
    completion:completed/received*100,wait:sum(week.wait.map((value,i)=>value*week.completed[i]))/completed,
    daily:completed/5,effort:hours/completed};
}
