/// <reference types="office-js" />

/**
 * WORD FORENSICS ENGINE
 */

type Snapshot = {
  time: number;
  words: number;
  paragraphCount: number;
  text: string;
};

type PasteEvent = {
    time: string;
    wordsAdded: number;
    seconds: number;
    wordsPerSecond: number;
    risk: string;
};

const timeline: Snapshot[] = [];
const pasteEvents: PasteEvent[] = []; 

let lastSnapshot: Snapshot | null = null;
let monitoring = false;
let lastTextHash = "";

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

  document.getElementById("export-btn")
    ?.addEventListener("click", exportReport);
});

/**
 * AUTO MONITOR
 */
function startMonitoring() {
  if (monitoring) return;
  monitoring = true;

  setInterval(() => {
    silentAnalyze();
  }, 1200);
}

/**
 * CORE ANALYSIS
 */
async function silentAnalyze() {
  await Word.run(async (context) => {

    const paragraphs = context.document.body.paragraphs;
    paragraphs.load("items/text");

    await context.sync();

    const texts = paragraphs.items.map(p => p.text);
    const fullText = texts.join(" ");

    const words = fullText
      .split(/\s+/)
      .filter(Boolean).length;

    const snapshot: Snapshot = {
      time: Date.now(),
      words,
      paragraphCount: texts.length,
      text: fullText
    };

    // IMPORTANT: ALWAYS RUN DETECTION (no hashing skip)
    detectPaste(snapshot);

    timeline.push(snapshot);

    updateDashboard(snapshot);

    await saveMetadata(snapshot);
  });
}
/**
 * SIMPLE HASH
 */
function simpleHash(str: string): string {
  let hash = 0;

  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }

  return hash.toString();
}

/**
 * PASTE DETECTION
 */
function detectPaste(current: Snapshot): void {

    if (!lastSnapshot) {
        lastSnapshot = current;
        return;
    }

    const seconds =
        (current.time - lastSnapshot.time) / 1000;

    if (seconds <= 0) {
        lastSnapshot = current;
        return;
    }

    const previousWords =
        lastSnapshot.text.split(/\s+/).filter(Boolean);

    const currentWords =
        current.text.split(/\s+/).filter(Boolean);

    const wordsAdded =
        currentWords.length - previousWords.length;

    if (wordsAdded <= 0) {
        lastSnapshot = current;
        return;
    }

    const charactersAdded =
        current.text.length - lastSnapshot.text.length;

    const wordsPerSecond =
        wordsAdded / seconds;

    let confidence = "";
    let percentage = 0;

    // ==================================================
    // RULE 1
    // Human typing rarely exceeds 3 words/sec.
    // ==================================================

    if (
        wordsAdded >= 10 &&
        wordsPerSecond >= 3
    ) {
        confidence = "LOW";
        percentage = 60;
    }

    // ==================================================
    // RULE 2
    // Very unlikely for a human.
    // ==================================================

    if (
        wordsAdded >= 20 &&
        wordsPerSecond >= 5
    ) {
        confidence = "MEDIUM";
        percentage = 75;
    }

    // ==================================================
    // RULE 3
    // Strong indication of pasted content.
    // ==================================================

    if (
        wordsAdded >= 40 &&
        wordsPerSecond >= 8
    ) {
        confidence = "HIGH";
        percentage = 90;
    }

    // ==================================================
    // RULE 4
    // Massive insertion.
    // ==================================================

    if (
        wordsAdded >= 80 ||
        charactersAdded >= 500
    ) {
        confidence = "VERY HIGH";
        percentage = 99;
    }

    if (confidence === "") {
        lastSnapshot = current;
        return;
    }

    console.log("=================================");
    console.log("SUSPICIOUS INSERTION DETECTED");
    console.log("Words Added:", wordsAdded);
    console.log("Characters Added:", charactersAdded);
    console.log("Elapsed Seconds:", seconds);
    console.log("Words / Second:", wordsPerSecond);
    console.log("Confidence:", confidence);
    console.log("=================================");

    pasteEvents.push({

        time: new Date(current.time).toLocaleTimeString(),

        wordsAdded,

        seconds,

        wordsPerSecond,

        risk: `${confidence} (${percentage}%)`

    });

    lastSnapshot = current;
}

/**
 * DASHBOARD
 */
function updateDashboard(snapshot: Snapshot) {

  const w = document.getElementById("word-count");
  if (w) w.textContent = snapshot.words.toString();

  const p = document.getElementById("paragraph-count");
  if (p) p.textContent = snapshot.paragraphCount.toString();

  const risk = calculateRiskScore();

  const riskBox = document.getElementById("forensic-alert");

  if (riskBox) {
    if (risk < 30) {
      riskBox.style.color = "green";
      riskBox.innerHTML = `🟢 LOW (${risk}/100)`;
    } else if (risk < 70) {
      riskBox.style.color = "orange";
      riskBox.innerHTML = `🟠 MEDIUM (${risk}/100)`;
    } else {
      riskBox.style.color = "red";
      riskBox.innerHTML = `🔴 HIGH (${risk}/100)`;
    }
  }

  renderReport(snapshot);
}

/**
 * RISK SCORE
 */
function calculateRiskScore(): number {

    let score = 0;

    pasteEvents.forEach(event => {

        switch(event.risk){

            case "LOW":
                score += 15;
                break;

            case "MEDIUM":
                score += 30;
                break;

            case "HIGH":
                score += 45;
                break;

            case "VERY HIGH":
                score += 60;
                break;

        }

    });

    return Math.min(score,100);

}

/**
 * METADATA SAVE (IMPORTANT)
 */
async function saveMetadata(snapshot: Snapshot) {

    await Word.run(async (context) => {

        const props = context.document.properties.customProperties;

        props.load("items");

        await context.sync();

        const forensicData = JSON.stringify({

            generated: new Date().toISOString(),

            timeline,

            pasteEvents,

            risk: calculateRiskScore(),

            snapshots: timeline.length

        });

        let found = false;

        props.items.forEach(p => {

            if (p.key === "ForensicsData") {

                p.delete();

                found = true;

            }

        });

        await context.sync();

        props.add("ForensicsData", forensicData);

        await context.sync();

    });

}

/**
 * REPORT
 */
function renderReport(snapshot: Snapshot) {

    const container =
        document.getElementById("report-container")!;

    let html = `

<h2>📄 Forensic Report</h2>

<p><b>Total Words:</b> ${snapshot.words}</p>

<p><b>Paragraphs:</b> ${snapshot.paragraphCount}</p>

<p><b>Snapshots:</b> ${timeline.length}</p>

<hr>

<h3>🚨 Copy-Paste Detection</h3>

`;

    if (pasteEvents.length == 0) {

        html += `

<div style="color:green">

No suspicious paste activity detected.

</div>

`;

    }

    else {

        pasteEvents.forEach((event,index)=>{

            html += `

<div style="
margin-top:10px;
padding:10px;
border-left:5px solid red;
background:#fff5f5">

<b>Paste Event ${index+1}</b><br>

Time:
${event.time}<br>

Words Added:
${event.wordsAdded}<br>

Duration:
${event.seconds.toFixed(2)} sec<br>

Speed:
${event.wordsPerSecond.toFixed(2)}
words/sec<br>

Confidence:
<b style="color:red">${event.risk}</b>

</div>

`;

        });

    }

    html += `

<hr>

<h3>🎯 Overall Risk</h3>

<h2>${calculateRiskScore()}/100</h2>

`;

    container.innerHTML = html;

}

/**
 * EXPORT JSON
 */
function exportReport(): void {

  const report = {
    generatedAt: new Date().toISOString(),
    timeline,
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