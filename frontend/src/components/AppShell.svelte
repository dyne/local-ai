<script>
  export let roles = [];
  export let activeRoleId = "voice";
  export let onSelectRole = () => {};

  function selectRole(roleId) {
    if (roleId !== activeRoleId) {
      onSelectRole(roleId);
    }
  }
</script>

<div class="layout">
  <aside class="role-nav">
    <h1>Local AI</h1>
    <p class="subtitle">Role workspace</p>
    <nav>
      {#each roles as role}
        <button
          class:active={role.id === activeRoleId}
          class="role-button"
          type="button"
          on:click={() => selectRole(role.id)}
        >
          <span class="label">{role.label}</span>
          <span class="meta">{role.status}</span>
        </button>
      {/each}
    </nav>
  </aside>

  <main class="content">
    <slot />
  </main>
</div>

<style>
  .layout {
    min-height: 100vh;
    display: grid;
    grid-template-columns: minmax(220px, 280px) 1fr;
    gap: 16px;
    padding: 16px;
    box-sizing: border-box;
  }

  .role-nav {
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

  @media (max-width: 900px) {
    .layout {
      grid-template-columns: 1fr;
      padding: 10px;
    }
  }
</style>

