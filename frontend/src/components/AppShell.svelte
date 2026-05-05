<script>
  export let roles = [];
  export let activeRoleId = "voice";
  export let onSelectRole = () => {};
  export let leftRailExpanded = true;
  export let rightRailExpanded = false;
  export let onToggleLeftRail = () => {};
  export let onToggleRightRail = () => {};

  function selectRole(roleId) {
    if (roleId !== activeRoleId) {
      onSelectRole(roleId);
    }
  }
</script>

<div class="layout" class:left-collapsed={!leftRailExpanded} class:right-collapsed={!rightRailExpanded}>
  <aside class="role-nav" aria-label="Role rail">
    <div class="rail-header">
      {#if leftRailExpanded}
        <div>
          <h1>Local AI</h1>
          <p class="subtitle">Role workspace</p>
        </div>
      {/if}
      <button type="button" class="rail-toggle" on:click={onToggleLeftRail} title="Toggle role rail">
        {leftRailExpanded ? "◀" : "▶"}
      </button>
    </div>
    <nav>
      {#each roles as role}
        <button
          class:active={role.id === activeRoleId}
          class="role-button"
          type="button"
          on:click={() => selectRole(role.id)}
        >
          <span class="label">{leftRailExpanded ? role.label : role.label.slice(0, 1)}</span>
          {#if leftRailExpanded}
            <span class="meta">{role.status}</span>
          {/if}
        </button>
      {/each}
    </nav>
  </aside>

  <main class="content">
    <slot />
  </main>
  <aside class="right-rail" aria-label="Log rail">
    <div class="rail-header right">
      <button type="button" class="rail-toggle" on:click={onToggleRightRail} title="Toggle log rail">
        {rightRailExpanded ? "▶" : "◀"}
      </button>
      {#if rightRailExpanded}
        <strong>Logs</strong>
      {/if}
    </div>
    <slot name="right-rail" />
  </aside>
</div>

<style>
  .layout {
    min-height: 100vh;
    display: grid;
    grid-template-columns: minmax(72px, 280px) 1fr minmax(72px, 360px);
    gap: 16px;
    padding: 16px;
    box-sizing: border-box;
  }

  .role-nav, .right-rail {
    border-radius: 18px;
    padding: 18px;
    background: rgba(255, 255, 255, 0.9);
    box-shadow: 0 10px 30px rgba(12, 37, 49, 0.12);
  }

  h1 {
    margin: 0;
    font-size: 1.4rem;
  }

  .subtitle {
    margin: 6px 0 14px;
    color: #495462;
    font-size: 0.9rem;
  }

  nav {
    display: grid;
    gap: 10px;
  }

  .role-button {
    border: 1px solid #c7d1d8;
    border-radius: 14px;
    background: #f9fbfc;
    text-align: left;
    padding: 10px 12px;
    cursor: pointer;
    display: grid;
    gap: 4px;
  }

  .role-button.active {
    border-color: #0d5f86;
    background: #e6f5fb;
  }

  .label {
    font-weight: 700;
  }

  .meta {
    text-transform: uppercase;
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    color: #566476;
  }

  .content {
    border-radius: 18px;
    padding: 20px;
    background: rgba(255, 255, 255, 0.92);
    box-shadow: 0 10px 30px rgba(12, 37, 49, 0.12);
  }

  .rail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
  }

  .rail-header.right {
    justify-content: flex-start;
  }

  .rail-toggle {
    border: 1px solid #bfcad3;
    background: #eef4f8;
    border-radius: 999px;
    width: 32px;
    height: 32px;
    cursor: pointer;
  }

  .left-collapsed .role-nav {
    padding: 12px;
  }

  .left-collapsed .role-button {
    justify-items: center;
    text-align: center;
  }

  .right-collapsed .right-rail {
    padding: 12px;
  }

  @media (max-width: 900px) {
    .layout {
      grid-template-columns: 1fr;
      padding: 10px;
    }
  }
</style>
