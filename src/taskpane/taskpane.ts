/// <reference types="office-js" />

/**
 * WORD FORENSICS ENGINE
 */

type Snapshot = {
    time: number;
    words: number;
    paragraphCount: number;
    text: string;

    fingerprint: string;

    wordsAdded: number;
    wordsDeleted: number;

    typingSpeed: number;

    suspicious: boolean;
};

type PasteEvent = {
    time: string;
    wordsAdded: number;
    seconds: number;
    wordsPerSecond: number;
    risk: string;
};

type EditingSession = {
    started: string;
    ended: string;

    totalSnapshots: number;

    totalWordsAdded: number;
    totalWordsDeleted: number;

    totalPasteEvents: number;

    highestRisk: number;

    averageTypingSpeed: number;

    finalWordCount: number;
};

const timeline: Snapshot[] = [];
const pasteEvents: PasteEvent[] = []; 
const FORENSICS_NAMESPACE = "urn:word-forensics-engine";

let lastSnapshot: Snapshot | null = null;
let monitoring = false;
let lastTextHash = "";

/**
 * APP START
 */
Office.onReady(async () => {
  const sideloadMsg = document.getElementById("sideload-msg");
  const appBody = document.getElementById("app-body");

  if (sideloadMsg) sideloadMsg.style.display = "none";
  if (appBody) appBody.style.display = "block";

  console.log("Word Forensics Ready");

  await loadMetadata();

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

/*
* function to load previuos data from last save if it does exist
*/
async function loadMetadata() {
  await Word.run(async (context) => {

    const parts = context.document.customXmlParts;

    parts.load("items");
    await context.sync();

    const existing = parts.items.find(p =>
      p.namespaceUri === FORENSICS_NAMESPACE
    );

    if (!existing) return;

    const xmlResult = existing.getXml();
    await context.sync();

    const xml = xmlResult.value;

    const parser = new DOMParser();
    const doc = parser.parseFromString(xml, "text/xml");

    const snapshots = Array.from(doc.getElementsByTagName("Snapshot"));
    const events = Array.from(doc.getElementsByTagName("PasteEvent"));

    timeline.length = 0;
    pasteEvents.length = 0;

    snapshots.forEach(s => {
      timeline.push({
        time: Number(s.getElementsByTagName("Time")[0]?.textContent || 0),
        words: Number(s.getElementsByTagName("Words")[0]?.textContent || 0),
        paragraphCount: Number(s.getElementsByTagName("Paragraphs")[0]?.textContent || 0),
        text: "",
        fingerprint: "",
        wordsAdded: 0,
        wordsDeleted: 0,
        typingSpeed: 0,
        suspicious: false
      });
    });

    events.forEach(e => {
      pasteEvents.push({
        time: e.getElementsByTagName("Time")[0]?.textContent || "",
        wordsAdded: Number(e.getElementsByTagName("WordsAdded")[0]?.textContent || 0),
        seconds: Number(e.getElementsByTagName("Seconds")[0]?.textContent || 0),
        wordsPerSecond: Number(e.getElementsByTagName("WordsPerSecond")[0]?.textContent || 0),
        risk: e.getElementsByTagName("Risk")[0]?.textContent || ""
      });
    });

    lastSnapshot =
      timeline.length ? timeline[timeline.length - 1] : null;

  });
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

        const fingerprint = await sha256(fullText);

        const words =
            fullText
                .split(/\s+/)
                .filter(Boolean)
                .length;

        const snapshot: Snapshot = {

            time: Date.now(),

            words,

            paragraphCount: texts.length,

            text: fullText,

            fingerprint,

            wordsAdded: 0,

            wordsDeleted: 0,

            typingSpeed: 0,

            suspicious: false

        };

        // Populate wordsAdded, typingSpeed, suspicious etc.
        detectPaste(snapshot);

        timeline.push(snapshot);

        updateDashboard(snapshot);

        await saveMetadata(snapshot);

    });

}

/**
 * editing session summary
 *
 */

async function sha256(text: string): Promise<string> {

    const encoder = new TextEncoder();

    const data = encoder.encode(text);

    const hashBuffer =
        await crypto.subtle.digest("SHA-256", data);

    const hashArray =
        Array.from(new Uint8Array(hashBuffer));

    return hashArray
        .map(b => b.toString(16).padStart(2,"0"))
        .join("");

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
        current.wordsAdded = 0;
        current.wordsDeleted = 0;
        current.typingSpeed = 0;
        current.suspicious = false;

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

    const wordDifference =
        currentWords.length - previousWords.length;

    // Store statistics inside the snapshot
    current.wordsAdded =
        wordDifference > 0 ? wordDifference : 0;

    current.wordsDeleted =
        wordDifference < 0 ? Math.abs(wordDifference) : 0;

    current.typingSpeed =
        seconds > 0 ? Math.abs(wordDifference) / seconds : 0;

    current.suspicious = false;

    // Nothing added
    if (wordDifference <= 0) {
        lastSnapshot = current;
        return;
    }

    const charactersAdded =
        current.text.length - lastSnapshot.text.length;

    const wordsPerSecond =
        wordDifference / seconds;

    let confidence = "";
    let percentage = 0;

    // Low confidence
    if (
        wordDifference >= 10 &&
        wordsPerSecond >= 3
    ) {
        confidence = "LOW";
        percentage = 60;
    }

    // Medium confidence
    if (
        wordDifference >= 20 &&
        wordsPerSecond >= 5
    ) {
        confidence = "MEDIUM";
        percentage = 75;
    }

    // High confidence
    if (
        wordDifference >= 40 &&
        wordsPerSecond >= 8
    ) {
        confidence = "HIGH";
        percentage = 90;
    }

    // Very high confidence
    if (
        wordDifference >= 80 ||
        charactersAdded >= 500
    ) {
        confidence = "VERY HIGH";
        percentage = 99;
    }

    if (confidence !== "") {

        current.suspicious = true;

        console.log("=================================");
        console.log("SUSPICIOUS INSERTION DETECTED");
        console.log("Words Added:", wordDifference);
        console.log("Characters Added:", charactersAdded);
        console.log("Elapsed Seconds:", seconds);
        console.log("Words / Second:", wordsPerSecond);
        console.log("Confidence:", confidence);
        console.log("=================================");

        pasteEvents.push({

            time: new Date(current.time).toLocaleTimeString(),

            wordsAdded: wordDifference,

            seconds,

            wordsPerSecond,

            risk: `${confidence} (${percentage}%)`

        });

    }

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

    const parts = context.document.customXmlParts;

    parts.load("items");
    await context.sync();

    let part = parts.items.find(p =>
      p.namespaceUri === FORENSICS_NAMESPACE
    );

    if (!part) {
      part = parts.add(`
        <Forensics xmlns="${FORENSICS_NAMESPACE}">
          <Timeline></Timeline>
          <PasteEvents></PasteEvents>
        </Forensics>
      `);
      await context.sync();
    }

    const xmlResult = part.getXml();
    await context.sync();

    let xml = xmlResult.value;

    // 🔥 SAFE STRING INSERTION (NO DOM APIs)
    const snapshotXml =
      `<Snapshot>` +
      `<Time>${snapshot.time}</Time>` +
      `<Words>${snapshot.words}</Words>` +
      `<Paragraphs>${snapshot.paragraphCount}</Paragraphs>` +
      `</Snapshot>`;

    xml = xml.replace("</Timeline>", snapshotXml + "</Timeline>");

    // Add paste event if needed
    const lastEvent = pasteEvents[pasteEvents.length - 1];

    if (lastEvent && snapshot.suspicious) {

      const eventXml =
        `<PasteEvent>` +
        `<Time>${lastEvent.time}</Time>` +
        `<WordsAdded>${lastEvent.wordsAdded}</WordsAdded>` +
        `<Seconds>${lastEvent.seconds}</Seconds>` +
        `<WordsPerSecond>${lastEvent.wordsPerSecond}</WordsPerSecond>` +
        `<Risk>${lastEvent.risk}</Risk>` +
        `</PasteEvent>`;

      xml = xml.replace("</PasteEvents>", eventXml + "</PasteEvents>");
    }

    part.setXml(xml);
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