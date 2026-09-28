/* Read-only projection of the persisted reviewer registry; never grants authority. */
globalThis.ReviewerStatus = (() => {
  const terminal = new Set(["APPLIED", "ACKNOWLEDGED", "NOT_REQUIRED", "RESOLVED_BY_CONFIRMATION", "HISTORICAL_NOT_REPLAYED", "NON_CONTROLLING"]);
  const labels = {
    QUEUED: "受付済み", WAITING_RESPONSE: "レビュー待ち", RESPONSE_RECEIVED: "応答受信・適用待ち",
    APPLYING: "Codexが適用中", APPLIED: "応答適用済み（次工程の許可とは別）",
    ACKNOWLEDGED: "受信確認済み（実行なし）", NOT_REQUIRED: "返信不要",
    HUMAN_REQUIRED: "人間判断待ち", CONTINUATION_FAILED: "継続処理失敗",
    RESOLVED_BY_CONFIRMATION: "確認報告で解決済み", HISTORICAL_NOT_REPLAYED: "過去記録・再実行対象外",
    NON_CONTROLLING: "参考記録・制御対象外", INVALIDATED: "失効・未適用"
  };
  const instant = value => typeof value === "string" && Number.isFinite(Date.parse(value)) ? Date.parse(value) : 0;
  const time = value => instant(value) ? new Date(value).toLocaleString("ja-JP", { timeZone: "Asia/Tokyo", hour12: false }) + " JST" : "時刻記録なし";
  const base = "https://github.com/HIPVG/AI-Control-Center-Review-Bridge";
  function rows(status) {
    return Object.entries(status.report_registry || {}).map(([id, entry]) => {
      const source = entry.response_file;
      let responseUrl = null;
      if (source && /^[a-f0-9]{40}$/.test(source.head_commit) && source.path === `poc/file-review-responses/${id}.md` && /^[A-Za-z0-9_-]+$/.test(id)) {
        responseUrl = `${base}/blob/${source.head_commit}/${source.path}`;
      } else if (Number.isSafeInteger(entry.response_comment_id) && entry.response_comment_id > 0) {
        responseUrl = `${base}/pull/1#issuecomment-${entry.response_comment_id}`;
      }
      const error = entry.file_error || entry.invalidation_reason || null;
      return { id, state: entry.state || "UNKNOWN", label: labels[entry.state] || `未分類: ${entry.state || "UNKNOWN"}`,
        active: Boolean(error) || !terminal.has(entry.state), error,
        timestamp: entry.updated_at || entry.applied_at || null, appliedAt: entry.applied_at || null,
        transport: entry.response_transport === "github_file" ? "ファイル" : "コメント",
        reportUrl: Number.isSafeInteger(entry.report_comment_id) && entry.report_comment_id > 0 ? `${base}/pull/1#issuecomment-${entry.report_comment_id}` : null,
        responseUrl, responseId: entry.response_file_id || entry.response_comment_id || null };
    }).sort((a, b) => instant(b.timestamp) - instant(a.timestamp) || a.id.localeCompare(b.id));
  }
  function health(status, now = Date.now()) {
    const stale = !instant(status.last_poll_at) || now - instant(status.last_poll_at) > (Math.max(10, Number(status.poll_seconds) || 120) * 2 + 60) * 1000;
    const state = status.last_error ? "Watcherエラー" : !status.running ? "Watcher停止" : !status.available ? "Watcher利用不可" : stale ? "取得時刻が古い・要確認" : "Watcher稼働中";
    return { state, detail: `最終PR取得: ${time(status.last_poll_at)} ／ 間隔: ${status.poll_seconds || "不明"}秒${status.last_error ? ` ／ ${status.last_error}` : ""}${stale && status.pending_response_report_id ? " ／ 継続処理中は取得が遅れる場合があります" : ""}` };
  }
  return { rows, health, time };
})();
