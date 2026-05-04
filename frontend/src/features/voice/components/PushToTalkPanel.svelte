<script>
  export let status = "idle";
  export let disabled = false;
  export let isRecording = false;
  export let toggleMode = false;
  export let onStart = async () => {};
  export let onStop = async () => {};
  export let onToggleMode = () => {};

  async function holdStart() {
    if (!toggleMode && !isRecording && !disabled) {
      await onStart();
    }
  }

  async function holdStop() {
    if (!toggleMode && isRecording) {
      await onStop();
    }
  }

  async function pressAction() {
    if (disabled) {
      return;
    }
    if (toggleMode) {
      if (isRecording) {
        await onStop();
      } else {
        await onStart();
      }
    }
  }

  async function onKeyDown(event) {
    if (event.key === " " || event.key === "Spacebar") {
      event.preventDefault();
      await pressAction();
    }
  }
</script>

<section class="ptt">
  <div class="row">
    <button class:recording={isRecording} class="mic" disabled={disabled} on:mousedown={() => void holdStart()} on:mouseup={() => void holdStop()} on:mouseleave={() => void holdStop()} on:touchstart={() => void holdStart()} on:touchend={() => void holdStop()} on:click={() => void pressAction()} on:keydown={onKeyDown}>
      {isRecording ? "Recording..." : "Push To Talk"}
    </button>
    <label class="toggle"><input type="checkbox" bind:checked={toggleMode} on:change={() => onToggleMode(toggleMode)} /> Toggle mode</label>
  </div>
  <p class="status">{status}</p>
</section>

