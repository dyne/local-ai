<script>
  export let notifications = [];
  export let onDismiss = () => {};
  export let onOpenLog = () => {};
</script>

<div class="notifications" aria-live="polite" aria-atomic="false">
  {#each notifications as item (item.key)}
    <aside class="toast">
      <div class="head">
        <strong>ERROR</strong>
        <span>{item.source}</span>
      </div>
      <p>{item.message}</p>
      <small>{item.timestamp} · {item.count}x</small>
      <button type="button" on:click={() => onOpenLog(item)}>Open in Logs</button>
      <button type="button" on:click={() => onDismiss(item.key)}>Dismiss</button>
    </aside>
  {/each}
</div>

<style>
  .notifications { position: fixed; right: 16px; bottom: 16px; display: grid; gap: 10px; z-index: 20; }
  .toast { width: min(340px, calc(100vw - 24px)); background: #fff3f3; border: 1px solid #d97d7d; border-radius: 12px; padding: 10px; box-shadow: 0 8px 20px rgba(0,0,0,0.12); }
  .head { display: flex; justify-content: space-between; font-size: 0.85rem; }
  p { margin: 6px 0; font-weight: 700; }
  small { color: #5a6774; }
  button { margin-top: 6px; }
</style>
