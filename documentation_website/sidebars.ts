import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docs: [
    'index',
    {
      type: 'category',
      label: '1. Getting Started',
      collapsed: false,
      items: [
        '1.1-what-is-cswon',
        '1.2-quickstart-miner',
        '1.3-quickstart-validator',
      ],
    },
    {
      type: 'category',
      label: '2. Architecture',
      items: [
        '2.1-architecture',
        '2.2-protocol',
        '2.3-dag-execution',
      ],
    },
    {
      type: 'category',
      label: '3. Incentive Design',
      items: [
        '3.1-emission-structure',
        '3.2-scoring-formula',
        '3.3-quality-scoring',
        '3.4-anti-gaming',
        '3.5-scoring-versioning',
      ],
    },
    {
      type: 'category',
      label: '4. Miner Guide',
      items: [
        '4.1-miner-registration',
        '4.2-workflow-plan',
        '4.3-miner-lifecycle',
        '4.4-early-participation',
      ],
    },
    {
      type: 'category',
      label: '5. Validator Guide',
      items: [
        '5.1-validator-hardware',
        '5.2-evaluation-pipeline',
        '5.3-weight-submission',
        '5.4-benchmark-governance',
        '5.5-exec-support-pool',
        '5.6-immunity-warmup',
      ],
    },
    {
      type: 'category',
      label: '6. Deployment & Operations',
      items: [
        '6.1-running-on-testnet',
        '6.2-running-on-mainnet',
        '6.3-running-on-staging',
        '6.4-local-deploy',
        '6.5-testnet-deploy',
      ],
    },
    {
      type: 'category',
      label: '7. Proof of Execution',
      collapsed: false,
      items: [
        '7.1-testnet-evidence',
        '7.2-validator-logs',
        '7.3-incentive-verification',
      ],
    },
    {
      type: 'category',
      label: '8. Economics & Roadmap',
      items: [
        '8.1-token-economy',
        '8.2-go-to-market',
        '8.3-roadmap',
      ],
    },
    {
      type: 'category',
      label: '9. Contributing',
      items: [
        '9.1-contributing',
      ],
    },
  ],
};

export default sidebars;
