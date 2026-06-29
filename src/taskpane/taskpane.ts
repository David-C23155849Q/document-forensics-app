/// <reference types="office-js" />

type Snapshot = {
  time: number;
  words: number;
  paragraphTexts: string[];
};

const timeline: Snapshot[] = [];

Office.onReady(() => {
  document.getElementById("app-body")!.style.display = "block";
  document.getElementById("sideload-msg")!.style.display = "none";

  document.getElementById("analyze-button")
    ?.addEventListener("click", analyzeDocument);

  document.getElementById("export-btn")
    ?.addEventListener("click", exportReport);

  startMonitoring();
});

/**
 * AUTO MONITOR
 */
function startMonitoring(): void {
  setInterval(() => {
    analyzeDocument();
  }, 3000);
}

/**
 * CORE ANALYSIS
 */
async function analyzeDocument() {
  await Word.run(async (context) => {
    const paragraphs = context.document.body.paragraphs;
    paragraphs.load("items/text");

    await context.sync();

    const texts = paragraphs.items.map(p => p.text);

    const words = texts.reduce((sum, t) =>
      sum + t.split(/\s+/).filter(Boolean).length, 0
    );

    const snapshot: Snapshot = {
      time: Date.now(),
      words,
      paragraphTexts: texts
    };

    timeline.push(snapshot);

    const duplicates = findDuplicateBlocks(texts);

    for (const d of duplicates) {
      await highlightParagraph(d.index, "yellow");
    }

    const risk = calculateRiskScore();

    renderReport({
      words,
      paragraphs: texts.length,
      duplicates,
      risk
    });
  });
}

/**
 * COPY-PASTE DETECTION
 */
function findDuplicateBlocks(paragraphs: string[]) {
  const matches: { index: number; text: string }[] = [];

  for (let i = 0; i < paragraphs.length; i++) {
    const current = paragraphs[i].trim().toLowerCase();

    if (!current || current.length < 40) continue;

    for (let j = 0; j < i; j++) {
      const prev = paragraphs[j].trim().toLowerCase();

      if (current === prev) {
        matches.push({
          index: i,
          text: paragraphs[i]
        });
        break;
      }
    }
  }

  return matches;
}

/**
 * HIGHLIGHT IN WORD
 */
async function highlightParagraph(index: number, color: string) {
  await Word.run(async (context) => {
    const paragraphs = context.document.body.paragraphs;
    paragraphs.load("items");

    await context.sync();

    const p = paragraphs.items[index];
    if (p) p.font.highlightColor = color;

    await context.sync();
  });
}

/**
 * RISK SCORE ENGINE
 */
function calculateRiskScore(): number {
  let score = 0;

  if (timeline.length < 2) return 0;

  for (let i = 1; i < timeline.length; i++) {
    const prev = timeline[i - 1];
    const curr = timeline[i];

    const dt = (curr.time - prev.time) / 1000;
    const dw = curr.words - prev.words;

    if (dw > 120 && dt < 10) score += 25;

    const wps = dt > 0 ? dw / dt : 0;
    if (wps > 8) score += 20;
  }

  return Math.min(score, 100);
}

/**
 * REPORT UI
 */
function renderReport(data: any) {
  const container =
    document.getElementById("report-container") ||
    (() => {
      const div = document.createElement("div");
      div.id = "report-container";
      document.getElementById("app-body")?.appendChild(div);
      return div;
    })();

  container.innerHTML = `
    <hr/>
    <h2>📊 Forensic Report</h2>

    <p><b>Words:</b> ${data.words}</p>
    <p><b>Paragraphs:</b> ${data.paragraphs}</p>

    <h3>🔴 Copy-Paste Detection</h3>

    ${
      data.duplicates.length
        ? data.duplicates.map((d: any, i: number) => `
            <div style="border-left:4px solid red;padding:6px;margin:6px 0;">
              <b>Match ${i + 1}</b><br/>
              Paragraph ${d.index + 1}
            </div>
          `).join("")
        : `<p style="color:green;">No duplicates detected</p>`
    }

    <h3>🎯 Risk Score</h3>
    <p style="font-size:18px;">
      ${data.risk}/100
    </p>
  `;
}

/**
 * EXPORT
 */
function exportReport() {
  const report = {
    generatedAt: new Date().toISOString(),
    snapshots: timeline.length,
    risk: calculateRiskScore()
  };

  const blob = new Blob([JSON.stringify(report, null, 2)], {
    type: "application/json"
  });

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");

  a.href = url;
  a.download = "forensic-report.json";
  a.click();

  URL.revokeObjectURL(url);
}