import React from "react";

/**
 * Minimal, safe Markdown renderer for lesson content (no raw HTML is ever injected).
 * Supports: ## headings, ``` code fences, | tables |, - / 1. lists, > quotes,
 * paragraphs, `inline code` and **bold**.
 */
function renderInline(text: string, keyBase: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const re = /(`[^`]+`|\*\*[^*]+\*\*)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let i = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith("`")) parts.push(<code key={`${keyBase}-c${i++}`} className="md-inline-code">{tok.slice(1, -1)}</code>);
    else parts.push(<strong key={`${keyBase}-b${i++}`}>{tok.slice(2, -2)}</strong>);
    last = m.index + tok.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

export const MarkdownLite: React.FC<{ source: string; className?: string }> = ({ source, className }) => {
  const lines = (source || "").replace(/\r\n/g, "\n").split("\n");
  const blocks: React.ReactNode[] = [];
  let i = 0;
  let k = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.trim().startsWith("```")) {
      const lang = line.trim().slice(3).trim();
      const body: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) body.push(lines[i++]);
      i++;
      blocks.push(
        <pre key={k++} className="md-code" data-lang={lang || undefined}>
          <code>{body.join("\n")}</code>
        </pre>
      );
      continue;
    }

    if (/^#{1,4}\s/.test(line)) {
      const level = line.match(/^#+/)![0].length;
      const text = line.replace(/^#+\s*/, "");
      blocks.push(level <= 2 ? <h3 key={k++} className="md-h">{renderInline(text, `h${k}`)}</h3> : <h4 key={k++} className="md-h4">{renderInline(text, `h${k}`)}</h4>);
      i++;
      continue;
    }

    if (line.trim().startsWith("|")) {
      const rows: string[][] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        const cells = lines[i].trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
        if (!cells.every((c) => /^:?-{2,}:?$/.test(c))) rows.push(cells);
        i++;
      }
      const [head, ...body] = rows;
      blocks.push(
        <div key={k++} className="md-table-wrap">
          <table className="md-table">
            <thead><tr>{head.map((c, j) => <th key={j}>{renderInline(c, `th${k}${j}`)}</th>)}</tr></thead>
            <tbody>{body.map((r, ri) => <tr key={ri}>{r.map((c, j) => <td key={j}>{renderInline(c, `td${k}${ri}${j}`)}</td>)}</tr>)}</tbody>
          </table>
        </div>
      );
      continue;
    }

    if (/^\s*(-|\d+\.)\s/.test(line)) {
      const ordered = /^\s*\d+\.\s/.test(line);
      const items: string[] = [];
      while (i < lines.length && /^\s*(-|\d+\.)\s/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*(-|\d+\.)\s/, ""));
        i++;
      }
      const children = items.map((it, j) => <li key={j}>{renderInline(it, `li${k}${j}`)}</li>);
      blocks.push(ordered ? <ol key={k++} className="md-list">{children}</ol> : <ul key={k++} className="md-list">{children}</ul>);
      continue;
    }

    if (line.trim().startsWith(">")) {
      blocks.push(<blockquote key={k++} className="md-quote">{renderInline(line.replace(/^\s*>\s?/, ""), `q${k}`)}</blockquote>);
      i++;
      continue;
    }

    if (!line.trim()) {
      i++;
      continue;
    }

    const para: string[] = [];
    while (i < lines.length && lines[i].trim() && !/^(#{1,4}\s|```|\||\s*(-|\d+\.)\s|>)/.test(lines[i].trim())) {
      para.push(lines[i].replace(/\s{2,}$/, ""));
      i++;
    }
    blocks.push(<p key={k++} className="md-p">{renderInline(para.join(" "), `p${k}`)}</p>);
  }

  return <div className={`markdown-lite ${className || ""}`}>{blocks}</div>;
};
