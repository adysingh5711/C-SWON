import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'C-SWON',
  tagline: 'Cross-Subnet Workflow Orchestration Network',
  favicon: 'img/favicon.ico',

  future: {
    v4: {
      removeLegacyPostBuildHeadAttribute: true,
    },
  },

  url: 'https://adysingh5711.github.io',
  baseUrl: '/C-SWON/',

  organizationName: 'adysingh5711',
  projectName: 'C-SWON',
  deploymentBranch: 'gh-pages',
  trailingSlash: false,

  onBrokenLinks: 'warn',

  markdown: {
    mermaid: true,
  },

  themes: ['@docusaurus/theme-mermaid'],

  plugins: [
    [
      require.resolve('@easyops-cn/docusaurus-search-local'),
      {
        hashed: true,
        language: ['en'],
        highlightSearchTermsOnTargetPage: true,
        searchResultLimits: 8,
        searchResultContextMaxLength: 50,
        docsRouteBasePath: '/docs',
        docsDir: '../docs',
        indexBlog: false,
      },
    ],
  ],

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          path: '../docs',
          routeBasePath: '/docs',
          sidebarPath: './sidebars.ts',
          sidebarCollapsible: true,
          editUrl: 'https://github.com/adysingh5711/C-SWON/edit/main/',
          showLastUpdateTime: true,
          exclude: [
            'superpowers/**',
            'stream_tutorial/**',
          ],
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  headTags: [
    {
      tagName: 'link',
      attributes: { rel: 'icon', type: 'image/svg+xml', href: '/C-SWON/img/favicon.svg' },
    },
    {
      tagName: 'link',
      attributes: { rel: 'apple-touch-icon', href: '/C-SWON/img/apple-touch-icon.png' },
    },
  ],

  themeConfig: {
    image: 'img/cswon-social-card.png',
    colorMode: {
      defaultMode: 'light',
      respectPrefersColorScheme: true,
    },
    mermaid: {
      theme: {
        dark: 'dark',
        light: 'default',
      },
      options: {
        fontFamily: 'DM Mono, monospace',
        fontSize: 14,
      },
    },
    navbar: {
      title: 'C-SWON',
      logo: {
        alt: 'C-SWON Logo',
        src: 'img/logo.png',
        style: { height: '28px', width: '28px', objectFit: 'contain' },
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docs',
          position: 'left',
          label: 'Docs',
        },
        {
          href: 'https://youtu.be/X2RZts7AXX0',
          label: 'Demo',
          position: 'right',
        },
        {
          href: 'https://github.com/adysingh5711/C-SWON',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            { label: 'Getting Started', to: '/docs/1.1-what-is-cswon' },
            { label: 'Miner Guide', to: '/docs/1.2-quickstart-miner' },
            { label: 'Validator Guide', to: '/docs/1.3-quickstart-validator' },
          ],
        },
        {
          title: 'Design',
          items: [
            { label: 'Architecture', to: '/docs/2.1-architecture' },
            { label: 'Scoring Formula', to: '/docs/3.2-scoring-formula' },
            { label: 'Anti-Gaming', to: '/docs/3.4-anti-gaming' },
          ],
        },
        {
          title: 'Community',
          items: [
            { label: 'GitHub', href: 'https://github.com/adysingh5711/C-SWON' },
            { label: 'Demo Video', href: 'https://youtu.be/X2RZts7AXX0' },
            { label: 'Hackathon', href: 'https://www.hackquest.io/hackathons/Bittensor-Subnet-Hackathon' },
          ],
        },
        {
          title: 'Evidence',
          items: [
            { label: 'Testnet Evidence', to: '/docs/7.1-testnet-evidence' },
            { label: 'Validator Logs', to: '/docs/7.2-validator-logs' },
            { label: 'Incentive Verification', to: '/docs/7.3-incentive-verification' },
          ],
        },
        {
          title: 'Contact',
          items: [
            { label: '✉ Email', href: 'mailto:singhaditya5711@gmail.com' },
            { label: '𝕏 Twitter / X', href: 'https://x.com/singhaditya5711' },
            { label: '✈ Telegram', href: 'https://t.me/singhaditya5711' },
            { label: '🔗 LinkedIn', href: 'https://www.linkedin.com/in/singhaditya5711/' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} C-SWON — Cross-Subnet Workflow Orchestration Network. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'json', 'python'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
