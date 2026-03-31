import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

const features = [
  {
    title: 'Miners',
    description: 'Design optimal multi-subnet workflow DAGs. Compete on task success, cost efficiency, and latency to earn Alpha emissions.',
    link: '/docs/1.2-quickstart-miner',
    linkText: 'QUICKSTART',
  },
  {
    title: 'Validators',
    description: 'Execute workflows in sandboxed Docker containers. Score miners with deterministic, reproducible metrics via a six-stage pipeline.',
    link: '/docs/1.3-quickstart-validator',
    linkText: 'QUICKSTART',
  },
  {
    title: 'Developers',
    description: 'Integrate C-SWON to route complex AI tasks across 100+ Bittensor subnets with a single API call.',
    link: '/docs/2.2-protocol',
    linkText: 'PROTOCOL SPEC',
  },
  {
    title: 'Judges',
    description: 'Transaction hashes, validator logs, and incentive verification — all on-chain evidence for the hackathon submission.',
    link: '/docs/7.1-testnet-evidence',
    linkText: 'VIEW EVIDENCE',
  },
];

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">Decentralised AI Workflow Router on Bittensor</p>
        <p style={{
          opacity: 0.7,
          fontSize: '16px',
          maxWidth: '640px',
          margin: '0 auto 2rem',
          fontWeight: 200,
          lineHeight: '160%',
        }}>
          The mined commodity is optimal workflow policy — which subnets to call,
          in what order, at the lowest cost and highest quality.
        </p>
        <div className={styles.buttons}>
          <Link
            className="button button--primary button--lg"
            to="/docs/1.1-what-is-cswon"
            style={{
              marginRight: '1rem',
              fontFamily: '"DM Mono", monospace',
              fontSize: '12px',
              letterSpacing: '0.6px',
              textTransform: 'uppercase',
              padding: '12px 32px',
            }}>
            Read the Docs
          </Link>
          <Link
            className="button button--outline button--lg"
            to="/docs/7.1-testnet-evidence"
            style={{
              fontFamily: '"DM Mono", monospace',
              fontSize: '12px',
              letterSpacing: '0.6px',
              textTransform: 'uppercase',
              padding: '12px 32px',
            }}>
            Testnet Evidence
          </Link>
        </div>
      </div>
    </header>
  );
}

function Feature({title, description, link, linkText}: {
  title: string; description: string; link: string; linkText: string;
}) {
  return (
    <div className={clsx('col col--3')} style={{marginBottom: '2rem'}}>
      <div style={{
        border: '1px solid var(--ifm-navbar-border, #dbdde1)',
        borderRadius: '8px',
        padding: '20px 24px',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}>
        <div>
          <Heading as="h3" style={{
            fontSize: '20px',
            fontWeight: 500,
            marginBottom: '12px',
          }}>{title}</Heading>
          <p style={{
            fontSize: '14px',
            color: 'var(--text-primary, #5f6368)',
            fontWeight: 200,
            lineHeight: '160%',
          }}>{description}</p>
        </div>
        <Link to={link} style={{
          fontFamily: '"DM Mono", monospace',
          fontSize: '0.75rem',
          fontWeight: 500,
          letterSpacing: '0.6px',
          textTransform: 'uppercase',
          textDecoration: 'none',
          marginTop: '16px',
          display: 'inline-block',
        }}>
          {linkText} →
        </Link>
      </div>
    </div>
  );
}

export default function Home(): ReactNode {
  return (
    <Layout
      title="Decentralised AI Workflow Router"
      description="C-SWON: Cross-Subnet Workflow Orchestration Network — Zapier for Bittensor Subnets">
      <HomepageHeader />
      <main>
        <section style={{padding: '3rem 0'}}>
          <div className="container">
            <div className="row">
              {features.map((props, idx) => (
                <Feature key={idx} {...props} />
              ))}
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
