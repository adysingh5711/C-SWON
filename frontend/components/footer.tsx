export function Footer() {
  return (
    <footer className="border-t border-[var(--border)] bg-[var(--surface-0)]/50 backdrop-blur-sm">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <div className="grid gap-8 sm:grid-cols-3">
          {/* Brand */}
          <div>
            <span className="font-mono text-sm font-bold text-[var(--teal)]">C-SWON</span>
            <p className="mt-2 text-sm text-[var(--ink-tertiary)]">
              Cross-Subnet Workflow Orchestration Network on Bittensor.
            </p>
          </div>

          {/* Resources */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-widest text-[var(--ink-muted)]">Resources</h3>
            <ul className="mt-3 space-y-2 text-sm">
              <li>
                <a href="https://adysingh5711.github.io/C-SWON/" target="_blank" rel="noopener noreferrer" className="text-[var(--ink-tertiary)] transition-colors hover:text-[var(--ink)]">
                  Documentation
                </a>
              </li>
              <li>
                <a href="https://github.com/adysingh5711/C-SWON" target="_blank" rel="noopener noreferrer" className="text-[var(--ink-tertiary)] transition-colors hover:text-[var(--ink)]">
                  GitHub Repository
                </a>
              </li>
              <li>
                <a href="https://docs.bittensor.com" target="_blank" rel="noopener noreferrer" className="text-[var(--ink-tertiary)] transition-colors hover:text-[var(--ink)]">
                  Bittensor Docs
                </a>
              </li>
            </ul>
          </div>

          {/* Network */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-widest text-[var(--ink-muted)]">Network</h3>
            <ul className="mt-3 space-y-2 text-sm">
              <li>
                <a href="https://taostats.io/subnets/netuid-26/" target="_blank" rel="noopener noreferrer" className="text-[var(--ink-tertiary)] transition-colors hover:text-[var(--ink)]">
                  Taostats (Subnet 26)
                </a>
              </li>
              <li>
                <a href="https://x.bittensor.com" target="_blank" rel="noopener noreferrer" className="text-[var(--ink-tertiary)] transition-colors hover:text-[var(--ink)]">
                  Bittensor Explorer
                </a>
              </li>
              <li>
                <a href="https://github.com/opentensor/bittensor-subnet-template" target="_blank" rel="noopener noreferrer" className="text-[var(--ink-tertiary)] transition-colors hover:text-[var(--ink)]">
                  Subnet Template
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 border-t border-[var(--border)] pt-6 text-center text-xs text-[var(--ink-muted)]">
          C-SWON — Testnet Subnet 26 on Bittensor
        </div>
      </div>
    </footer>
  );
}
