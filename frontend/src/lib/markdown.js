export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderInline(value) {
  return escapeHtml(value)
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>')
    .replace(/\$\$([^$]+)\$\$/g, '<span class="math-inline">$1</span>')
    .replace(/(^|[^\\])\$([^$\n]+)\$/g, '$1<span class="math-inline">$2</span>')
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

function isTableLine(line) {
  const trimmed = line.trim();
  return trimmed.includes("|") && (trimmed.startsWith("|") || trimmed.endsWith("|"));
}

function isTableSeparator(line) {
  const cells = splitTableRow(line);
  return cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell.trim()));
}

function splitTableRow(line) {
  let trimmed = line.trim();
  if (trimmed.startsWith("|")) trimmed = trimmed.slice(1);
  if (trimmed.endsWith("|")) trimmed = trimmed.slice(0, -1);
  return trimmed.split("|").map((cell) => cell.trim());
}

function renderTable(tableLines) {
  const rows = tableLines.map(splitTableRow);
  const hasSeparator = rows.length > 1 && isTableSeparator(tableLines[1]);
  const header = rows[0] || [];
  const body = hasSeparator ? rows.slice(2) : rows.slice(1);

  if (!header.length) return "";

  const headerHtml = `<thead><tr>${header
    .map((cell) => `<th>${renderInline(cell)}</th>`)
    .join("")}</tr></thead>`;
  const bodyHtml = body.length
    ? `<tbody>${body
        .map((row) => `<tr>${row.map((cell) => `<td>${renderInline(cell)}</td>`).join("")}</tr>`)
        .join("")}</tbody>`
    : "";
  return `<div class="table-wrap"><table>${headerHtml}${bodyHtml}</table></div>`;
}

export function renderMarkdown(markdown) {
  const lines = String(markdown || "").replace(/\r\n/g, "\n").split("\n");
  const html = [];
  let paragraph = [];
  let list = [];
  let listType = "ul";
  let inCode = false;
  let codeLines = [];
  let inMath = false;
  let mathLines = [];

  const flushParagraph = () => {
    if (!paragraph.length) return;
    html.push(`<p>${renderInline(paragraph.join(" "))}</p>`);
    paragraph = [];
  };

  const flushList = () => {
    if (!list.length) return;
    html.push(`<${listType}>${list.map((item) => `<li>${renderInline(item)}</li>`).join("")}</${listType}>`);
    list = [];
    listType = "ul";
  };

  for (let index = 0; index < lines.length; index += 1) {
    const rawLine = lines[index];
    const line = rawLine.trimEnd();
    const trimmed = line.trim();

    if (trimmed.startsWith("```")) {
      if (inCode) {
        html.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
        codeLines = [];
        inCode = false;
      } else {
        flushParagraph();
        flushList();
        inCode = true;
      }
      continue;
    }

    if (inCode) {
      codeLines.push(rawLine);
      continue;
    }

    if (trimmed === "$$") {
      if (inMath) {
        html.push(`<div class="math-block">${escapeHtml(mathLines.join("\n"))}</div>`);
        mathLines = [];
        inMath = false;
      } else {
        flushParagraph();
        flushList();
        inMath = true;
      }
      continue;
    }

    if (inMath) {
      mathLines.push(rawLine);
      continue;
    }

    const singleLineMath = /^\$\$(.+)\$\$$/.exec(trimmed);
    if (singleLineMath) {
      flushParagraph();
      flushList();
      html.push(`<div class="math-block">${escapeHtml(singleLineMath[1].trim())}</div>`);
      continue;
    }

    if (!trimmed) {
      flushParagraph();
      flushList();
      continue;
    }

    if (/^---+$/.test(trimmed)) {
      flushParagraph();
      flushList();
      html.push("<hr>");
      continue;
    }

    if (isTableLine(trimmed)) {
      flushParagraph();
      flushList();
      const tableLines = [trimmed];
      while (index + 1 < lines.length && isTableLine(lines[index + 1])) {
        index += 1;
        tableLines.push(lines[index].trim());
      }
      html.push(renderTable(tableLines));
      continue;
    }

    const heading = /^(#{1,4})\s+(.+)$/.exec(trimmed);
    if (heading) {
      flushParagraph();
      flushList();
      const level = heading[1].length;
      html.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
      continue;
    }

    const quote = /^>\s?(.+)$/.exec(trimmed);
    if (quote) {
      flushParagraph();
      flushList();
      html.push(`<blockquote>${renderInline(quote[1])}</blockquote>`);
      continue;
    }

    const bullet = /^[-*]\s+(.+)$/.exec(trimmed);
    if (bullet) {
      flushParagraph();
      if (list.length && listType !== "ul") flushList();
      listType = "ul";
      list.push(bullet[1]);
      continue;
    }

    const ordered = /^\d+[.)]\s+(.+)$/.exec(trimmed);
    if (ordered) {
      flushParagraph();
      if (list.length && listType !== "ol") flushList();
      listType = "ol";
      list.push(ordered[1]);
      continue;
    }

    paragraph.push(trimmed);
  }

  flushParagraph();
  flushList();

  if (inCode) html.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
  if (inMath) html.push(`<div class="math-block">${escapeHtml(mathLines.join("\n"))}</div>`);

  return html.join("");
}
