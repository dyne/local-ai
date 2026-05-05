<script>
  import { onDestroy, onMount, tick } from "svelte";

  import AppShell from "./components/AppShell.svelte";
  import DocumentsWorkspace from "./features/documents/DocumentsWorkspace.svelte";
  import ErrorNotifications from "./features/logs/ErrorNotifications.svelte";
  import LogPanel from "./features/logs/LogPanel.svelte";
  import { createLogStore } from "./features/logs/log-store";
  import { upsertErrorNotification } from "./features/logs/notifications";
  import VoiceTranscription from "./features/voice/VoiceTranscription.svelte";
  import { fallbackRoles, parseRolesResponse } from "./lib/roles";
  import { readUiPreferences, writeLeftRailExpanded, writeRightLogRailExpanded } from "./lib/ui-preferences";

  let roles = fallbackRoles();
  let activeRoleId = "voice";
  $: activeRole = roles.find((item) => item.id === activeRoleId);

  const logStore = createLogStore({ maxHistory: 500 });
  let allLogs = [];
  let visibleLogs = [];
  let logLevel = "";
  let logSource = "";
  let logQuery = "";
  let autoScrollLogs = true;
  let leftRailExpanded = true;
  let rightLogRailExpanded = false;
  let selectedLogEventId = "";
  let notifications = [];

  $: visibleLogs = logStore.filterEvents({ level: logLevel, source: logSource, query: logQuery });
  $: logSources = [...new Set(allLogs.map((item) => item.source))].sort();

  function selectRole(roleId) {
    activeRoleId = roleId;
  }

  function dismissNotification(key) {
    notifications = notifications.filter((item) => item.key !== key);
  }

  function pushNotification(event) {
    notifications = upsertErrorNotification(notifications, event, { maxVisible: 4 });
  }

  function toggleLeftRail() {
    leftRailExpanded = !leftRailExpanded;
    writeLeftRailExpanded(leftRailExpanded);
  }

  function toggleRightLogRail() {
    rightLogRailExpanded = !rightLogRailExpanded;
    writeRightLogRailExpanded(rightLogRailExpanded);
  }

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

  let unsubscribe = () => {};
  let closeLive = () => {};

  onMount(() => {
    const prefs = readUiPreferences();
    leftRailExpanded = prefs.leftRailExpanded;
    rightLogRailExpanded = prefs.rightLogRailExpanded;
    unsubscribe = logStore.subscribe(async (events) => {
      const newest = events[events.length - 1];
      allLogs = events;
      if (newest) {
        pushNotification(newest);
      }
      if (autoScrollLogs) {
        await tick();
        const rows = document.querySelector(".log-panel .rows");
        rows?.scrollTo({ top: rows.scrollHeight });
      }
    });

    void loadRoles();
    void logStore.loadHistory().catch(() => {});
    closeLive = logStore.connectLive();
  });

  onDestroy(() => {
    unsubscribe();
    closeLive();
  });
</script>

<svelte:head>
  <title>Local AI</title>
</svelte:head>

<div class="app">
  <AppShell
    {roles}
    {activeRoleId}
    onSelectRole={selectRole}
    {leftRailExpanded}
    rightRailExpanded={rightLogRailExpanded}
    onToggleLeftRail={toggleLeftRail}
    onToggleRightRail={toggleRightLogRail}
  >
    {#if activeRoleId === "voice"}
      <VoiceTranscription />
    {:else if activeRoleId === "documents"}
      <DocumentsWorkspace />
    {:else}
      <section class="placeholder">
        <p class="eyebrow">Role</p>
        <h2>{activeRole?.label ?? "Role"}</h2>
        <p>{activeRole?.summary ?? "This workspace is planned but not yet implemented."}</p>
        <p class="state">Status: {activeRole?.status ?? "planned"}</p>
      </section>
    {/if}

    <svelte:fragment slot="right-rail">
      <LogPanel
        events={visibleLogs}
        level={logLevel}
        source={logSource}
        query={logQuery}
        autoScroll={autoScrollLogs}
        sources={logSources}
        collapsed={!rightLogRailExpanded}
        selectedEventId={selectedLogEventId}
        onExpand={() => {
          rightLogRailExpanded = true;
          writeRightLogRailExpanded(true);
        }}
        onSelectEvent={(id) => (selectedLogEventId = id)}
        onLevelChange={(value) => (logLevel = value)}
        onSourceChange={(value) => (logSource = value)}
        onQueryChange={(value) => (logQuery = value)}
        onClearView={() => logStore.clearView()}
        onToggleAutoScroll={(value) => (autoScrollLogs = value)}
      />
    </svelte:fragment>
  </AppShell>

  <ErrorNotifications
    {notifications}
    onDismiss={dismissNotification}
    onOpenLog={(item) => {
      rightLogRailExpanded = true;
      writeRightLogRailExpanded(true);
      logLevel = "ERROR";
      logQuery = item?.message || "";
    }}
  />
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: "Segoe UI", sans-serif;
    background: linear-gradient(135deg, #eef7fb 0%, #f7f2e8 42%, #e9edf5 100%);
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
