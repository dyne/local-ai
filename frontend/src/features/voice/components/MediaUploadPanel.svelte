<script>
  export let uploadState = "idle";
  export let uploadError = "";
  export let localPath = "";
  export let onLocalPathChange = () => {};
  export let onTranscribePath = async () => {};
</script>

<section class="upload">
  <div class="drop-zone" role="region" aria-label="Local media transcription path input" aria-describedby="media-upload-hint">
    <label for="local-media-path"><strong>Local media file path</strong></label>
    <input
      id="local-media-path"
      type="text"
      value={localPath}
      placeholder="C:\media\sample.wav"
      on:input={(event) => onLocalPathChange(event.currentTarget.value)}
    />
    <button type="button" on:click={onTranscribePath}>Transcribe Local File</button>
    <p class="hint" id="media-upload-hint">Use a real local filesystem path. Browser file inputs often return fake paths.</p>
  </div>
  <p class="status">Local transcription state: {uploadState}</p>
  {#if uploadError}
    <p class="error">{uploadError}</p>
  {/if}
</section>
