/// <reference types="office-js" />

type Snapshot = {
  time: number;
  words: number;
  paragraphCount: number;
  text: string;
};

const timeline: Snapshot[] = [];

let lastSnapshot: Snapshot | null = null;

let monitoringInterval: number | null = null;

/**
 * APP START
 */
Office.onReady(() => {
  const sideloadMsg = document.getElementById("sideload-msg");
  const appBody = document.getElementById("app-body");

  if (sideloadMsg) sideloadMsg.style.display = "none";
  if (appBody) appBody.style.display = "block";

  console.log("Word Forensics Ready");

  startMonitoring();

  document.getElementById("analyze-button")
    ?.addEventListener("click", analyzeDocument);

  document.getElementById("export-btn")
    ?.addEventListener("click", exportReport);
});

/**
 * AUTO MONITOR
 */
function startMonitoring(): void {
  if (monitoringInterval) return;

  monitoringInterval = window.setInterval(() => {
    analyzeDocument();
  }, 3000);
}

/**
 * CORE ANALYSIS
 */
async function analyzeDocument(): Promise<void> {
  await Word.run(async (context) => {
    const paragraphs = context.document.body.paragraphs;
    paragraphs.load("items/text");

    await context.sync();

    const items = paragraphs.items;

    const paragraphTexts = items.map(p => p.text);

    const wordsPerParagraph = paragraphTexts.map(p =>
      p.trim().split(/\s+/).filter(Boolean).length
    );

    const totalWords = wordsPerParagraph.reduce((a, b) => a + b, 0);

    const snapshot: Snapshot = {
      time: Date.now(),
      words: totalWords,
      paragraphCount: items.length,
      text: paragraphTexts.join("\n"),
    };

    timeline.push(snapshot);

    // =========================
    // COPY-PASTE DETECTION
    // =========================
    const copyPasteHits: string[] = [];

    for (let i = 1; i < wordsPerParagraph.length; i++) {
      const diff = wordsPerParagraph[i] - wordsPerParagraph[i - 1];

      if (diff > 60) {
        copyPasteHits.push(`Paragraph ${i + 1} sudden jump (+${diff} words)`);
      }
    }

    // =========================
    // SECTION ANALYSIS
    // =========================
    const sections: any[] = [];
    const chunkSize = 3;

    for (let i = 0; i < wordsPerParagraph.length; i += chunkSize) {
      const slice = wordsPerParagraph.slice(i, i + chunkSize);
      const words = slice.reduce((a, b) => a + b, 0);

      const prev =
        i > 0
          ? wordsPerParagraph.slice(i - chunkSize, i).reduce((a, b) => a + b, 0)
          : words;

      const jump = words - prev;

      sections.push({
        index: sections.length + 1,
        words,
        risk: jump > 80 ? 80 : jump > 40 ? 50 : 10,
      });
    }

    const estimatedTime = Math.round(totalWords / 200);

    const risk = calculateRiskScore();

    renderReport({
      words: totalWords,
      paragraphs: items.length,
      estimatedTime,
      copyPasteHits,
      sections,
      risk,
    });
  });
}

/**
 * RISK SCORE
 */
function calculateRiskScore(): number {
  let score = 0;

  for (let i = 1; i < timeline.length; i++) {
    const prev = timeline[i - 1];
    const curr = timeline[i];

    const timeDiff = (curr.time - prev.time) / 1000;
    const wordDiff = curr.words - prev.words;

    if (wordDiff > 120 && timeDiff < 10) score += 25;
    if (Math.abs(curr.paragraphCount - prev.paragraphCount) > 3) score += 15;

    const wps = timeDiff > 0 ? wordDiff / timeDiff : 0;
    if (wps > 8) score += 20;

    const wordsArray = curr.text.toLowerCase().split(/\s+/);
    const uniqueRatio =
      wordsArray.length > 0 ? new Set(wordsArray).size / wordsArray.length : 1;

    if (uniqueRatio < 0.45 && curr.words > 120) score += 20;
  }

  return Math.min(score, 100);
}

/**
 * UI REPORT
 */
function renderReport(data: any) {
  let container = document.getElementById("report-container");

  if (!container) {
    container = document.createElement("div");
    container.id = "report-container";
    document.getElementById("app-body")?.appendChild(container);
  }

  container.innerHTML = `
    <hr/>
    <h2>📄 Forensic Report</h2>

    <p><b>Words:</b> ${data.words}</p>
    <p><b>Paragraphs:</b> ${data.paragraphs}</p>
    <p><b>Estimated Time:</b> ~${data.estimatedTime} min</p>

    <h3>⚠ Copy-Paste Detection</h3>
    ${
      data.copyPasteHits.length
        ? data.copyPasteHits.map((h: string) => `<p style="color:red;">${h}</p>`).join("")
        : "<p style='color:green;'>No suspicious activity detected</p>"
    }

    <h3>📊 Sections</h3>
    ${data.sections
      .map(
        (s: any) => `
        <div style="margin-bottom:8px;">
          <b>Section ${s.index}</b><br/>
          Words: ${s.words}<br/>
          Risk: ${s.risk > 50 ? "🔴 High" : "🟢 Low"}
        </div>
      `
      )
      .join("")}

    <h3>🎯 Risk Score</h3>
    <p style="font-size:18px;">
      ${data.risk < 30
        ? "🟢 LOW"
        : data.risk < 70
        ? "🟠 MEDIUM"
        : "🔴 HIGH"
      } (${data.risk}/100)
    </p>
  `;
}

/**
 * EXPORT REPORT
 */
function exportReport(): void {
  const report = {
    generatedAt: new Date().toISOString(),
    snapshots: timeline.length,
    risk: calculateRiskScore(),
  };

  const blob = new Blob([JSON.stringify(report, null, 2)], {
    type: "application/json",
  });

  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "forensic-report.json";
  a.click();

  URL.revokeObjectURL(url);
}