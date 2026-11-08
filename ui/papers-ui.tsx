// SPDX-License-Identifier: CeCILL-2.1 OR AGPL-3.0-or-later
import { Component, useEffect, useState, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { StatTile } from "nirs4all-ui/qualification";

interface PublishedMetric {
  name: string;
  valueText: string;
  partition: string | null;
}

interface PaperProjection {
  readingStatus: string;
  readingExplanation: string;
  rawDownloadSha256: string;
  coreContainerSha256?: string;
  coreManifestSha256?: string;
  ownerProfile?: string;
  metrics: PublishedMetric[];
}

function partitionLabel(partition: string | null): string {
  if (partition === null) return "Partition not supplied";
  return partition === "" ? "Partition supplied as an empty string" : partition;
}

function PaperSummary({ data, onReady }: { data: PaperProjection; onReady: () => void }) {
  const [selected, setSelected] = useState(-1);
  const partitions = Array.from(new Set(data.metrics.map((metric) => metric.partition)));
  const visible = data.metrics.map((metric, index) => ({ metric, index })).filter(
    ({ metric }) => selected === -1 || metric.partition === partitions[selected],
  );
  useEffect(onReady, [onReady]);

  return (
    <>
      <h3>Reading and identities</h3>
      <div className="papers-ui-grid">
        <StatTile label="Current reading" value={data.readingStatus}
          hint={data.readingExplanation} tone="neutral" className="papers-ui-text" />
        <StatTile label="Execution" value="Not evaluated"
          hint="Papers does not load fitted objects" tone="neutral" className="papers-ui-text" />
        <StatTile label="Raw downloadable file SHA-256" value={<code>{data.rawDownloadSha256}</code>}
          hint="Original download identity" tone="neutral" className="papers-ui-identity" />
        {data.coreContainerSha256 && <StatTile label="Core container SHA-256"
          value={<code>{data.coreContainerSha256}</code>} tone="neutral" className="papers-ui-identity" />}
        {data.coreManifestSha256 && <StatTile label="Core manifest SHA-256"
          value={<code>{data.coreManifestSha256}</code>} tone="neutral" className="papers-ui-identity" />}
        {data.ownerProfile && <StatTile label="Owner profile" value={data.ownerProfile}
          tone="neutral" className="papers-ui-text" />}
      </div>
      <h3>Results — as published</h3>
      {partitions.length > 1 && (
        <div className="papers-ui-controls">
          <label htmlFor="papers-partition">Published result partition</label>
          <select id="papers-partition" value={selected} aria-controls="papers-published-cards"
            onChange={(event) => setSelected(Number(event.target.value))}>
            <option value={-1}>All published results</option>
            {partitions.map((partition, index) => (
              <option value={index} key={index}>{partitionLabel(partition)}</option>
            ))}
          </select>
          <button id="papers-reset" type="button" onClick={() => setSelected(-1)}>Reset</button>
        </div>
      )}
      <p id="papers-result-count" role="status" aria-live="polite" aria-atomic="true">
        {visible.length} / {data.metrics.length} published results shown
      </p>
      {data.metrics.length === 0 && <p>No published scores recorded. Missing owner scores are not reconstructed.</p>}
      <div id="papers-published-cards" className="papers-ui-grid">
        {visible.map(({ metric, index }) => (
          <StatTile key={index} label={metric.name} value={metric.valueText} tone="neutral"
            hint={`As published · ${partitionLabel(metric.partition)}`} />
        ))}
      </div>
      <p>These cards do not recompute scores. Complete static results and owner documents remain available on this page.</p>
    </>
  );
}

class StaticFallback extends Component<
  { children: ReactNode; restore: () => void }, { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch() { this.props.restore(); }
  render() { return this.state.failed ? null : this.props.children; }
}

const host = document.getElementById("papers-ui");
const payload = document.getElementById("papers-ui-data");
const staticResults = document.getElementById("papers-static-results");
if (host && payload && staticResults instanceof HTMLDetailsElement) {
  const restore = () => { host.hidden = true; staticResults.open = true; };
  const reveal = () => { host.hidden = false; staticResults.open = false; };
  try {
    const data = JSON.parse(payload.textContent ?? "") as PaperProjection;
    createRoot(host).render(
      <StaticFallback restore={restore}><PaperSummary data={data} onReady={reveal} /></StaticFallback>,
    );
  } catch {
    restore();
  }
}
