<script>
  import { onMount } from "svelte";

  import AppShell from "./components/AppShell.svelte";
  import VoiceTranscription from "./features/voice/VoiceTranscription.svelte";
  import { fallbackRoles, parseRolesResponse } from "./lib/roles";

  let roles = fallbackRoles();
  let activeRoleId = "voice";
  $: activeRole = roles.find((item) => item.id === activeRoleId);

  async function loadRoles() {
    try {
      const response = await fetch("/api/app/roles");
      if (!response.ok) {
        return;
      }
      const payload = await response.json();
      roles = parseRolesResponse(payload);
      if (!roles.some((role) => role.id === activeRoleId)) {
        activeRoleId = roles[0]?.id ?? "voice";
      }
    } catch {
      // Keep fallback roles when endpoint is unavailable.
    }
  }

  function selectRole(roleId) {
    activeRoleId = roleId;
  }

  onMount(() => {
    void loadRoles();
  });
</script>

<svelte:head>
  <title>Local AI</title>
</svelte:head>

<div class="app">
  <AppShell {roles} {activeRoleId} onSelectRole={selectRole}>
    {#if activeRoleId === "voice"}
      <VoiceTranscription />
    {:else}
      <section class="placeholder">
        <p class="eyebrow">Role</p>
        <h2>{activeRole?.label ?? "Role"}</h2>
        <p>{activeRole?.summary ?? "This workspace is planned but not yet implemented."}</p>
        <p class="state">Status: {activeRole?.status ?? "planned"}</p>
      </section>
    {/if}
  </AppShell>
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: "Segoe UI", sans-serif;
    background:
      linear-gradient(135deg, #eef7fb 0%, #f7f2e8 42%, #e9edf5 100%);
    color: #1e2330;
  }

  .app {
    min-height: 100vh;
  }

  .placeholder {
    max-width: 760px;
  }

  .eyebrow {
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    font-size: 0.74rem;
    color: #4f5f74;
    font-weight: 700;
  }

  h2 {
    margin: 8px 0 10px;
    font-size: 1.8rem;
  }

  .state {
    margin-top: 18px;
    font-weight: 700;
    color: #2f5b70;
  }
</style>
