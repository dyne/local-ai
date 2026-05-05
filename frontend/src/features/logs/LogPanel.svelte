<script>
  export let events = [];
  export let level = "";
  export let source = "";
  export let query = "";
  export let autoScroll = true;
  export let sources = [];
  export let onLevelChange = () => {};
  export let onSourceChange = () => {};
  export let onQueryChange = () => {};
  export let onClearView = () => {};
  export let onToggleAutoScroll = () => {};

  function copyEvent(item) {
    const text = `${item.timestamp} ${item.level} ${item.source} ${item.message}${item.details?.length ? ` | ${item.details.join(" ")}` : ""}`;
    navigator.clipboard?.writeText(text);
  }
</script>

<section class="log-panel">
  <header>
    <h3>App Logs</h3>
    <button type="button" on:click={onClearView}>Clear View</button>
  </header>
  <div class="filters">
    <input placeholder="Search logs" value={query} on:input={(e) => onQueryChange(e.currentTarget.value)} />
    <select value={level} on:change={(e) => onLevelChange(e.currentTarget.value)}>
      <option value="">All levels</option>
      <option value="ERROR">ERROR</option>
      <option value="WARNING">WARNING</option>
      <option value="INFO">INFO</option>
      <option value="DEBUG">DEBUG</option>
    </select>
    <select value={source} on:change={(e) => onSourceChange(e.currentTarget.value)}>
      <option value="">All sources</option>
      {#each sources as sourceName}
        <option value={sourceName}>{sourceName}</option>
      {/each}
    </select>
    <label class="toggle"><input type="checkbox" checked={autoScroll} on:change={(e) => onToggleAutoScroll(e.currentTarget.checked)} /> Auto-scroll</label>
  </div>
  <div class="rows">
    {#if events.length === 0}
      <p class="empty">No logs yet.</p>
    {:else}
      {#each events as item}
        <article class="row" class:error={item.level === "ERROR"}>
          <div class="meta">{item.timestamp} <strong>{item.level}</strong> {item.source}</div>
          <div class="message">{item.message}</div>
          {#if item.details?.length}
            <div class="details">{item.details.join(" | ")}</div>
          {/if}
          <button type="button" class="copy" on:click={() => copyEvent(item)}>Copy</button>
        </article>
      {/each}
    {/if}
  </div>
</section>

<style>
  .log-panel { margin-top: 16px; border: 1px solid #d2dbe2; border-radius: 14px; padding: 12px; background: #f8fbfd; }
  header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
  h3 { margin: 0; }
  .filters { display: grid; grid-template-columns: 1fr 140px 180px auto; gap: 8px; margin-bottom: 10px; }
  .filters input, .filters select { border: 1px solid #cbd7e0; border-radius: 10px; padding: 8px; font: inherit; }
  .toggle { display: flex; align-items: center; gap: 6px; font-size: 0.9rem; }
  .rows { max-height: 260px; overflow: auto; display: grid; gap: 8px; }
  .row { background: #fff; border: 1px solid #e2e8ef; border-radius: 10px; padding: 8px; }
  .row.error { border-color: #d98888; background: #fff5f5; }
  .meta { font-size: 0.8rem; color: #4a5f72; }
  .message { margin-top: 4px; font-weight: 600; }
  .details { margin-top: 4px; color: #3f5568; font-size: 0.9rem; }
  .copy { margin-top: 6px; }
  .empty { margin: 0; color: #4b6073; }

  @media (max-width: 900px) {
    .filters { grid-template-columns: 1fr; }
  }
</style>
