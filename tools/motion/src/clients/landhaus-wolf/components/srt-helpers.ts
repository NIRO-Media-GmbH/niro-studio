/** Parse SRT timestamp "HH:MM:SS,mmm" to seconds */
export const t = (srtTime: string): number => {
  const [h, m, rest] = srtTime.split(":");
  const [s, ms] = rest.split(",");
  return Number(h) * 3600 + Number(m) * 60 + Number(s) + Number(ms) / 1000;
};
