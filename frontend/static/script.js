let audioContext;
let processor;
let input;
let stream;

let recordedData = [];
let sentences = [];
let current = 0;

let stats = {
    correct: 0,
    mispronounced: 0,
    missing: 0,
    weak: []
};

const diffScreen = document.getElementById("difficulty-screen");
const sessScreen = document.getElementById("session-screen");
const sumScreen = document.getElementById("summary-screen");
const sentenceBox = document.getElementById("sentence-box");
const progress = document.getElementById("progress");
const feedbackBox = document.getElementById("feedback");
const nextBtn = document.getElementById("next-btn");

document.querySelectorAll(".level-btn").forEach(btn => {
    btn.onclick = () => startSession(btn.dataset.level);
});

async function startSession(level) {
    diffScreen.classList.add("hidden");
    sessScreen.classList.remove("hidden");

    const res = await fetch(`/get-sentences?level=${level}&count=10`);
    const data = await res.json();
    sentences = data.sentences.map(s => s.text);
    loadSentence();
}

function loadSentence() {
    progress.innerText = `Sentence ${current+1} / ${sentences.length}`;
    sentenceBox.innerText = sentences[current];
    feedbackBox.innerHTML = "";
    nextBtn.classList.add("hidden");
    enableRecording(true);
}

function enableRecording(enable) {
    document.getElementById("record-btn").disabled = !enable;
    document.getElementById("stop-btn").disabled = enable;
}

document.getElementById("record-btn").onclick = async () => {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    audioContext = new AudioContext({ sampleRate: 16000 });
    input = audioContext.createMediaStreamSource(stream);
    processor = audioContext.createScriptProcessor(4096, 1, 1);

    recordedData = [];

    processor.onaudioprocess = (e) => {
        recordedData.push(new Float32Array(e.inputBuffer.getChannelData(0)));
    };

    input.connect(processor);
    processor.connect(audioContext.destination);

    enableRecording(false);
};

document.getElementById("stop-btn").onclick = async () => {
    processor.disconnect();
    input.disconnect();
    stream.getTracks().forEach(t => t.stop());

    const wavBlob = createWavBlob(recordedData, 16000);
    await evaluateAudio(wavBlob);
};

async function evaluateAudio(blob) {
    const form = new FormData();
    form.append("sentence", sentences[current]);
    form.append("audio", blob, "audio.wav");

    const res = await fetch("/evaluate", { method: "POST", body: form });
    const data = await res.json();
    showFeedback(data.results);
}

function showFeedback(results) {
    feedbackBox.innerHTML = "";
    results.forEach(r => {
        let span = document.createElement("span");
        span.innerText = r.word + " ";

        if (r.status === "CORRECT") {
            span.className = "correct";
            stats.correct++;
        } else if (r.status === "MISPRONOUNCED") {
            span.className = "mispronounced";
            stats.mispronounced++;
            stats.weak.push(r.word);
        } else if (r.status === "NOT SPOKEN") {
            span.className = "not-spoken";
            stats.missing++;
        }
        feedbackBox.appendChild(span);
    });

    nextBtn.classList.remove("hidden");
}

nextBtn.onclick = () => {
    current++;
    if (current >= sentences.length) showSummary();
    else loadSentence();
};

function showSummary() {
    sessScreen.classList.add("hidden");
    sumScreen.classList.remove("hidden");

    document.getElementById("sum-correct").innerText = `Correct: ${stats.correct}`;
    document.getElementById("sum-wrong").innerText = `Mispronounced: ${stats.mispronounced}`;
    document.getElementById("sum-missing").innerText = `Missing: ${stats.missing}`;
    document.getElementById("sum-weak").innerText = `Weak Words: ${[...new Set(stats.weak)].join(", ")}`;
}

function createWavBlob(buffers, sampleRate) {
    let samples = mergeBuffers(buffers);
    let wavBytes = encodeWAV(samples, sampleRate);
    return new Blob([wavBytes], { type: "audio/wav" });
}

function mergeBuffers(buffers) {
    let length = buffers.reduce((acc, b) => acc + b.length, 0);
    let merged = new Float32Array(length);
    let offset = 0;
    buffers.forEach(b => {
        merged.set(b, offset);
        offset += b.length;
    });
    return merged;
}

function encodeWAV(samples, sampleRate) {
    let buffer = new ArrayBuffer(44 + samples.length * 2);
    let view = new DataView(buffer);

    writeString(view, 0, "RIFF");
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(view, 8, "WAVE");
    writeString(view, 12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(view, 36, "data");
    view.setUint32(40, samples.length * 2, true);

    let offset = 44;
    for (let i = 0; i < samples.length; i++) {
        let s = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        offset += 2;
    }
    return buffer;
}

function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}
