<script>
  export let saveSample = false;
  export let silenceDetect = true;
  export let echoCancellation = false;
  export let noiseSuppression = false;
  export let autoGainControl = false;
  export let clientDebug = false;
  export let vadMode = "3";
  export let chunkSeconds = "1.5";
  export let overlapSeconds = "0.00";
</script>

<div class="grid">
  <label><input type="checkbox" bind:checked={saveSample} /> Save WAV capture</label>
  <label><input type="checkbox" bind:checked={silenceDetect} /> Voice enhance</label>
  <label><input type="checkbox" bind:checked={echoCancellation} /> Echo cancellation</label>
  <label><input type="checkbox" bind:checked={noiseSuppression} /> Noise suppression</label>
  <label><input type="checkbox" bind:checked={autoGainControl} /> Auto gain control</label>
  <label><input type="checkbox" bind:checked={clientDebug} /> Client debug</label>
  <label>VAD<select bind:value={vadMode}><option value="0">0</option><option value="1">1</option><option value="2">2</option><option value="3">3</option></select></label>
  <label>Chunk (s)<input bind:value={chunkSeconds} type="number" min="0.2" step="0.1" /></label>
  <label>Overlap (s)<input bind:value={overlapSeconds} type="number" min="0.0" step="0.05" /></label>
</div>

