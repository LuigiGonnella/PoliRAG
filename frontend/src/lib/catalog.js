import { courseLabel, degreeLabel, groupLabel, t, yearLabel } from "./i18n.js";

export function buildCourseGroups(catalog) {
  const groups = [];
  for (const degree of catalog?.degrees || []) {
    for (const year of degree.years || []) {
      groups.push({
        key: yearKey(degree.value, year.value),
        degree,
        year,
        courses: year.courses || [],
      });
    }
  }
  return groups;
}

export function yearKey(degreeValue, yearValue) {
  return `${degreeValue || ""}::${yearValue || ""}`;
}

export function findGroup(groups, keyOrSession) {
  if (!keyOrSession) return null;
  if (typeof keyOrSession === "string") return groups.find((group) => group.key === keyOrSession) || null;
  return (
    groups.find(
      (group) =>
        group.degree.value === keyOrSession.degree_filter && group.year.value === keyOrSession.year_filter,
    ) || null
  );
}

export function findCourse(groups, courseValue, degreeValue = null, yearValue = null) {
  for (const group of groups) {
    if (degreeValue && group.degree.value !== degreeValue) continue;
    if (yearValue && group.year.value !== yearValue) continue;
    const course = group.courses.find((item) => item.value === courseValue);
    if (course) return { group, course };
  }
  return null;
}

export function scopeLabel(session, groups, language = "en") {
  if (!session) return t("generalKnowledgeBase", language);
  if (session.course_filter) {
    const match = findCourse(groups, session.course_filter, session.degree_filter, session.year_filter);
    return match ? courseLabel(match.course, language) : courseLabel(session.course_filter, language);
  }
  if (session.year_filter) {
    const group = findGroup(groups, session);
    return group
      ? `${groupLabel(group, language)} / ${t("scopeAllCourses", language)}`
      : `${degreeLabel(session.degree_filter, language) || "Year"} / ${yearLabel(
          session.year_filter,
          language,
        )} / ${t("scopeAllCourses", language)}`;
  }
  return t("general", language);
}

export function sessionScopeLabel(session, groups, language = "en") {
  if (session.course_filter) {
    const match = findCourse(groups, session.course_filter, session.degree_filter, session.year_filter);
    return match ? courseLabel(match.course, language) : courseLabel(session.course_filter, language);
  }
  if (session.year_filter) {
    const group = findGroup(groups, session);
    return group ? `${yearLabel(group.year.value, language)} - ${t("scopeAllCourses", language)}` : t("year", language);
  }
  return t("general", language);
}
