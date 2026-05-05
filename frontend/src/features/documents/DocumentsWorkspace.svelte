<script>
  import { onMount } from "svelte";

  import { getJson, postJson, summarizeHealth } from "./api";

  let sourcePath = "";
  let sourceMessage = "";
  let queryText = "";
  let queryError = "";
  let statusError = "";
  let indexError = "";
  let answer = "";
  let evidence = [];
  let warnings = [];
  let sources = [];
  let selectedDocument = null;

  let recollHealth = { status: "unknown", error: "" };
  let redisHealth = { status: "unknown", error: "" };
  let ovmsHealth = { status: "unknown", error: "" };

  async function loadStatus() {
    statusError = "";
    try {
      const [statusPayload, recollPayload, redisPayload, ovmsPayload] = await Promise.all([
        getJson("/api/documents/status"),
        getJson("/api/documents/health/recoll"),
        getJson("/api/documents/health/redis"),
        getJson("/api/documents/health/ovms"),
      ]);
      sources = statusPayload.sources ?? [];
      recollHealth = summarizeHealth(recollPayload);
      redisHealth = summarizeHealth(redisPayload);
      ovmsHealth = summarizeHealth(ovmsPayload);
      if (ovmsPayload.setup_command) {
        ovmsHealth = { ...ovmsHealth, setupCommand: ovmsPayload.setup_command };
      }
    } catch (error) {
      statusError = String(error?.message || error);
    }
  }

  async function addSource() {
    sourceMessage = "";
    indexError = "";
    try {
      const payload = await postJson("/api/documents/sources", { path: sourcePath });
      sourceMessage = payload.message || "Source added.";
      sourcePath = "";
      await loadStatus();
    } catch (error) {
      sourceMessage = String(error?.message || error);
    }
  }

  async function runIndex(rebuild) {
    indexError = "";
    try {
      const payload = await postJson("/api/documents/index", { rebuild });
      if (payload.message) {
        sourceMessage = payload.message;
      }
      await loadStatus();
    } catch (error) {
      indexError = String(error?.message || error);
    }
  }

  async function submitQuery() {
    queryError = "";
    selectedDocument = null;
    try {
      const payload = await postJson("/api/documents/query", { query: queryText });
      answer = payload.answer || "";
      evidence = payload.evidence || [];
      warnings = payload.warnings || [];
    } catch (error) {
      queryError = String(error?.message || error);
    }
  }

  async function openDocument(documentId) {
    try {
      selectedDocument = await getJson(`/api/documents/${documentId}`);
    } catch (error) {
      queryError = String(error?.message || error);
    }
  }

  onMount(() => {
    void loadStatus();
  });
</script>

<section class="workspace">
  <header>
    <h2>Documents</h2>
    <p>Query indexed local archives with lexical and semantic refinement.</p>
  </header>

  <section class="status-grid">
    <article>
      <h3>Recoll</h3>
      <p>Status: {recollHealth.status}</p>
      {#if recollHealth.error}<p class="error">{recollHealth.error}</p>{/if}
    </article>
    <article>
      <h3>Redis</h3>
      <p>Status: {redisHealth.status}</p>
      {#if redisHealth.error}<p class="error">{redisHealth.error}</p>{/if}
    </article>
    <article>
      <h3>OVMS</h3>
      <p>Status: {ovmsHealth.status}</p>
      {#if ovmsHealth.error}<p class="error">{ovmsHealth.error}</p>{/if}
      {#if ovmsHealth.setupCommand}
        <code>{ovmsHealth.setupCommand}</code>
      {/if}
    </article>
  </section>

  {#if statusError}<pre class="error-block">{statusError}</pre>{/if}

  <section class="panel">
    <h3>Sources</h3>
    <div class="row">
      <input bind:value={sourcePath} placeholder="C:\archive\notes" />
      <button type="button" on:click={addSource}>Add Source</button>
      <button type="button" on:click={() => runIndex(false)}>Index</button>
      <button type="button" on:click={() => runIndex(true)}>Rebuild</button>
    </div>
    {#if sourceMessage}<pre class="info-block">{sourceMessage}</pre>{/if}
    {#if indexError}<pre class="error-block">{indexError}</pre>{/if}
    <ul>
      {#each sources as source}
        <li><strong>{source.label || source.source_id}</strong> - {source.root_path}</li>
      {/each}
    </ul>
  </section>

  <section class="panel">
    <h3>Query</h3>
    <div class="row">
      <input bind:value={queryText} placeholder="Ask about indexed content" />
      <button type="button" on:click={submitQuery}>Run Query</button>
    </div>
    {#if queryError}<pre class="error-block">{queryError}</pre>{/if}
    {#if warnings.length > 0}
      <ul>
        {#each warnings as warning}
          <li>{warning}</li>
        {/each}
      </ul>
    {/if}
    {#if answer}
      <article class="answer">
        <h4>Answer</h4>
        <p>{answer}</p>
      </article>
    {/if}
    <h4>Evidence</h4>
    <ul>
      {#each evidence as item}
        <li>
          <button type="button" on:click={() => openDocument(item.document_id)}>
            [{item.citation_id}] {item.source_path}
          </button>
        </li>
      {/each}
    </ul>
  </section>

  {#if selectedDocument?.document}
    <section class="panel">
      <h3>Document Preview</h3>
      <p><strong>{selectedDocument.document.title || selectedDocument.document.document_id}</strong></p>
      <p>{selectedDocument.document.source_path}</p>
      <pre>{selectedDocument.document.text}</pre>
    </section>
  {/if}
</section>

<style>
  .workspace { display: grid; gap: 14px; }
  header h2 { margin: 0; }
  header p { margin: 4px 0 0; color: #475467; }
  .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }
  article, .panel { border: 1px solid #d7dfe7; border-radius: 10px; padding: 12px; background: #fff; }
  .row { display: flex; gap: 8px; flex-wrap: wrap; }
  input { flex: 1; min-width: 220px; border: 1px solid #c8d2dc; border-radius: 8px; padding: 8px; font: inherit; }
  button { border: 1px solid #96a6b7; border-radius: 8px; padding: 8px 10px; background: #f5f8fb; font: inherit; cursor: pointer; }
  .error { color: #9a2f2f; font-weight: 600; }
  .info-block, .error-block {
    margin: 8px 0 0;
    border-radius: 8px;
    padding: 8px 10px;
    white-space: pre-wrap;
    overflow: auto;
    user-select: text;
    -webkit-user-select: text;
  }
  .info-block {
    border: 1px solid #d7dfe7;
    background: #f8fafc;
    color: #1f2937;
  }
  .error-block {
    border: 1px solid #ef9a9a;
    background: #fff1f1;
    color: #7f1d1d;
    max-height: 180px;
  }
  ul { margin: 8px 0 0; padding-left: 18px; }
  code { display: block; white-space: pre-wrap; margin-top: 6px; font-size: 0.8rem; }
  pre { max-height: 240px; overflow: auto; background: #0f172a; color: #e2e8f0; padding: 10px; border-radius: 8px; }
</style>
