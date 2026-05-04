<script>
  import { pickFirstMediaFile } from "../media-file";

  export let uploadState = "idle";
  export let uploadError = "";
  export let onUploadFile = async () => {};

  let isDragOver = false;

  async function handleInputChange(event) {
    const file = pickFirstMediaFile(event.target.files);
    if (file) {
      await onUploadFile(file);
    }
    event.target.value = "";
  }

  async function handleDrop(event) {
    event.preventDefault();
    isDragOver = false;
    const file = pickFirstMediaFile(event.dataTransfer?.files);
    if (file) {
      await onUploadFile(file);
    }
  }

  async function handlePaste(event) {
    const file = pickFirstMediaFile(event.clipboardData?.files);
    if (file) {
      event.preventDefault();
      await onUploadFile(file);
    }
  }
</script>

<section class="upload" on:paste={handlePaste}>
  <div class:drag-over={isDragOver} class="drop-zone" role="region" aria-label="Media upload drop zone" aria-describedby="media-upload-hint" on:dragover|preventDefault={() => (isDragOver = true)} on:dragleave={() => (isDragOver = false)} on:drop={handleDrop}>
    <label class="picker">
      <input type="file" accept="audio/*,video/*,.wav,.mp3,.m4a,.ogg,.webm,.mp4,.mov,.mkv,.flac,.aac" on:change={handleInputChange} />
      Choose Audio/Video File
    </label>
    <p>Or drag/drop, or paste a clipboard file.</p>
    <p class="hint" id="media-upload-hint">Supports audio or video files supported by this build.</p>
  </div>
  <p class="status">Upload state: {uploadState}</p>
  {#if uploadError}
    <p class="error">{uploadError}</p>
  {/if}
</section>
