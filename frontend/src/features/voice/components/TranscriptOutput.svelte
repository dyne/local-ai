<script>
  export let lines = [];
  export let onClear = () => {};
</script>

<section class="transcript">
  <div class="transcript-header">
    <h3>Transcript</h3>
    <button class="clear" on:click={onClear}>Clear</button>
  </div>
  <pre>{lines.join("\n")}</pre>
</section>

