<script>
  import { onDestroy } from "svelte";

  import { readRuntimeConfig } from "../../lib/runtime-config";
  import {
    buildSessionPayload,
    CHUNK_TIMESLICE_MS,
    preferredMimeType,
    TARGET_AUDIO_BITRATE,
    wsBaseUrl,
  } from "../../lib/session-payload";
  import MediaUploadPanel from "./components/MediaUploadPanel.svelte";
  import PushToTalkPanel from "./components/PushToTalkPanel.svelte";
  import TranscriptOutput from "./components/TranscriptOutput.svelte";
  import VoiceSettings from "./components/VoiceSettings.svelte";

  const runtimeConfig = readRuntimeConfig(window);

  let saveSample = false;
  let silenceDetect = runtimeConfig.silenceDetectDefault;
  let echoCancellation = false;
  let noiseSuppression = false;
  let autoGainControl = false;
  let clientDebug = false;
  let vadMode = String(runtimeConfig.vadModeDefault);
  let chunkSeconds = "1.5";
  let overlapSeconds = "0.00";
  let status = "idle";
  let transcriptLines = [];
  let toggleMode = false;
  let uploadState = "idle";
  let uploadError = "";
  let uploadResults = [];

  let stream = null;
  let eventSource = null;
  let audioSocket = null;
  let mediaRecorder = null;
  let sessionId = null;
  let sentBlobCount = 0;

  function appendLine(value) {
    transcriptLines = [...transcriptLines, value];
  }

  function appendClientDebug(value) {
    if (clientDebug) {
      appendLine(value);
    }
  }

  function isRecording() {
    return Boolean(stream);
  }

  async function start() {
    if (isRecording()) {
      return;
    }
    try {
      sessionId = globalThis.crypto?.randomUUID ? globalThis.crypto.randomUUID() : String(Date.now());
      status = "requesting-mic";

      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 48000,
          echoCancellation,
          noiseSuppression,
          autoGainControl,
        },
        video: false,
      });

      const mimeType = preferredMimeType();
      if (!mimeType) {
        throw new Error("No supported Opus MediaRecorder MIME type");
      }
      const response = await fetch("/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          buildSessionPayload({
            sessionId,
            saveSample,
            silenceDetect,
            debug: clientDebug,
            vadMode,
            chunkSeconds,
            overlapSeconds,
            mimeType,
            audioBitrate: TARGET_AUDIO_BITRATE,
          }),
        ),
      });
      if (!response.ok) {
        throw new Error(`Session setup failed: ${await response.text()}`);
      }
      eventSource = new EventSource(`/events/${sessionId}`);
      eventSource.onmessage = (event) => appendLine(event.data);
      eventSource.onerror = () => (status = "error");

      audioSocket = new WebSocket(`${wsBaseUrl()}/audio/${sessionId}`);
      await new Promise((resolve, reject) => {
        audioSocket.onopen = resolve;
        audioSocket.onerror = () => reject(new Error("Audio socket failed to open"));
      });
      appendClientDebug("[client] audio websocket open");
      mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: TARGET_AUDIO_BITRATE,
      });
      mediaRecorder.ondataavailable = async (event) => {
        if (!event.data || event.data.size === 0) {
          return;
        }
        if (audioSocket?.readyState === WebSocket.OPEN) {
          sentBlobCount += 1;
          audioSocket.send(await event.data.arrayBuffer());
        }
      };
      mediaRecorder.start(CHUNK_TIMESLICE_MS);
      status = "recording";
    } catch (error) {
      status = "error";
      appendLine(`[error] ${String(error?.message || error)}`);
      await stop();
      status = "error";
    }
  }

  async function stop() {
    if (!isRecording()) {
      return;
    }
    status = "stopping";
    if (mediaRecorder) {
      try {
        if (mediaRecorder.state !== "inactive") {
          mediaRecorder.stop();
        }
      } catch {}
      mediaRecorder = null;
    }
    if (audioSocket) {
      try {
        audioSocket.close();
      } catch {}
      audioSocket = null;
    }
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    if (sessionId) {
      try {
        await fetch(`/session/${sessionId}`, { method: "DELETE" });
      } catch {}
    }
    sessionId = null;
    sentBlobCount = 0;
    status = "idle";
  }

  async function uploadFile(file) {
    uploadState = "uploading";
    uploadError = "";
    try {
      const response = await fetch(`/api/voice/transcriptions?silence_detect=${silenceDetect ? "true" : "false"}&vad_mode=${encodeURIComponent(vadMode)}`, {
        method: "POST",
        headers: {
          "x-source-name": file.name,
          "content-type": file.type || "application/octet-stream",
        },
        body: await file.arrayBuffer(),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        const reason = payload?.detail?.reason || "Upload failed.";
        const details = payload?.detail?.details?.join(" ") || "";
        throw new Error(`${reason} ${details}`.trim());
      }
      uploadState = "done";
      const payload = await response.json();
      uploadResults = [
        {
          source_name: payload.source_name,
          text: payload.text,
          status: "done",
        },
        ...uploadResults,
      ].slice(0, 8);
      if (payload.text) {
        appendLine(`[upload:${payload.source_name}] ${payload.text}`);
      }
    } catch (error) {
      uploadState = "error";
      uploadError = String(error?.message || error);
      uploadResults = [{ source_name: file.name, text: uploadError, status: "error" }, ...uploadResults].slice(0, 8);
    }
  }

  onDestroy(() => {
    void stop();
  });
</script>

<section class="hero">
  <p class="eyebrow">Role</p>
  <h2>Voice Transcription</h2>
  <p class="lede">Push-to-talk for live audio plus upload, drag/drop, and paste for media files.</p>
</section>

<section class="controls">
  <PushToTalkPanel
    status={status}
    isRecording={isRecording()}
    onStart={start}
    onStop={stop}
    bind:toggleMode
    onToggleMode={(value) => (toggleMode = value)}
  />
  <MediaUploadPanel {uploadState} {uploadError} onUploadFile={uploadFile} />
  <VoiceSettings bind:saveSample bind:silenceDetect bind:echoCancellation bind:noiseSuppression bind:autoGainControl bind:clientDebug bind:vadMode bind:chunkSeconds bind:overlapSeconds />
</section>

<TranscriptOutput lines={transcriptLines} onClear={() => (transcriptLines = [])} />

{#if uploadResults.length > 0}
  <section class="history">
    <h3>Recent Upload Results</h3>
    <ul>
      {#each uploadResults as result}
        <li>
          <strong>{result.source_name}</strong> [{result.status}]<br />
          {result.text}
        </li>
      {/each}
    </ul>
  </section>
{/if}

<style>
  .hero { margin-bottom: 20px; }
  .eyebrow { margin: 0 0 4px; text-transform: uppercase; letter-spacing: 0.08em; color: #476276; font-size: 0.72rem; font-weight: 700; }
  h2 { margin: 0; font-size: 1.7rem; }
  .lede { margin: 8px 0 0; color: #405262; }
  .controls { display: grid; gap: 14px; margin-bottom: 18px; }
  :global(.grid) { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px 14px; }
  :global(label) { display: grid; gap: 6px; font-weight: 600; }
  :global(input[type="number"]), :global(select) { border: 1px solid #cdd5df; border-radius: 10px; padding: 9px 10px; font: inherit; background: #fff; }
  :global(button) { border: 0; border-radius: 999px; padding: 10px 16px; font: inherit; font-weight: 700; cursor: pointer; }
  :global(button:disabled) { opacity: 0.55; cursor: not-allowed; }
  :global(.transcript) { border-radius: 16px; background: #111827; color: #e5eef8; padding: 16px; }
  :global(.transcript-header) { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
  :global(pre) { margin: 0; white-space: pre-wrap; min-height: 260px; max-height: 52vh; overflow: auto; font-family: "Cascadia Code", "SFMono-Regular", monospace; font-size: 0.92rem; line-height: 1.45; }
  :global(.clear) { background: #9c2f2f; color: #fff; }
  :global(.ptt .mic) { background: #176c3f; color: #fff; min-width: 200px; }
  :global(.ptt .mic.recording) { background: #aa2d2d; }
  :global(.ptt .row) { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
  :global(.ptt .status) { color: #475467; font-weight: 700; margin: 6px 0 0; }
  :global(.upload .drop-zone) { border: 2px dashed #98a9b6; border-radius: 12px; padding: 12px; background: #f7fbff; }
  :global(.upload .drop-zone.drag-over) { border-color: #0d6d93; background: #eaf8ff; }
  :global(.upload .picker input) { display: none; }
  :global(.upload .picker) { display: inline-block; background: #0d6d93; color: #fff; border-radius: 999px; padding: 10px 14px; cursor: pointer; font-weight: 700; }
  :global(.upload .hint) { color: #4a5d6a; font-size: 0.9rem; }
  :global(.upload .status) { margin-top: 8px; font-weight: 700; color: #42556a; }
  :global(.upload .error) { color: #9c2f2f; font-weight: 700; }
  .history { margin-top: 14px; }
  .history ul { margin: 8px 0 0; padding-left: 18px; }
  .history li { margin-bottom: 8px; }
</style>

