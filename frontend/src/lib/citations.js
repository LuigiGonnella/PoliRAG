export function normalizeSourceName(source) {
  const clean = String(source || "source").replaceAll("\\", "/");
  return clean.split("/").filter(Boolean).pop() || clean;
}

export function dedupeCitations(citations = []) {
  const seen = new Map();

  for (const citation of citations) {
    const source = normalizeSourceName(citation.source || citation.type || "source");
    const key = `${citation.type || "local"}::${source.toLowerCase()}`;
    const current =
      seen.get(key) ||
      {
        ...citation,
        source,
        pages: new Set(),
        score: Number(citation.score || 0),
      };

    const page = citation.page && citation.page !== "Unknown" ? String(citation.page) : "";
    for (const item of page.split(",").map((value) => value.trim()).filter(Boolean)) {
      current.pages.add(item);
    }

    const score = Number(citation.score || 0);
    if (score > Number(current.score || 0)) current.score = score;
    seen.set(key, current);
  }

  return [...seen.values()].map((citation) => {
    const pages = [...citation.pages].sort((a, b) => Number(a) - Number(b));
    const { pages: _pages, ...rest } = citation;
    return { ...rest, page: pages.join(", ") };
  });
}
