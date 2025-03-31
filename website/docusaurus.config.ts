import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: 'VibeCopilot',
  tagline: '智能项目管理助手',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://jacobcy.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/VibeCopilot/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'jacobcy', // Usually your GitHub org/user name.
  projectName: 'VibeCopilot', // Usually your repo name.

  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'zh-Hans',
    locales: ['zh-Hans', 'en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/jacobcy/VibeCopilot/tree/main/website/',
          routeBasePath: '/', // 让文档作为默认首页显示
        },
        blog: {
          showReadingTime: true,
          feedOptions: {
            type: ['rss', 'atom'],
            xslt: true,
          },
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/jacobcy/VibeCopilot/tree/main/website/',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Replace with your project's social card
    image: 'img/docusaurus-social-card.jpg',
    navbar: {
      title: 'VibeCopilot',
      logo: {
        alt: 'VibeCopilot Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: '文档',
        },
        {
          to: '/user/guides/getting_started',
          label: '快速入门',
          position: 'left'
        },
        {
          to: '/user/tutorials/',
          label: '教程',
          position: 'left'
        },
        {
          to: '/dev/architecture',
          label: '开发文档',
          position: 'left'
        },
        {
          to: '/blog',
          label: '博客',
          position: 'left'
        },
        {
          href: 'https://github.com/jacobcy/VibeCopilot',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: '文档',
          items: [
            {
              label: '快速入门',
              to: '/user/guides/getting_started',
            },
            {
              label: 'Obsidian集成',
              to: '/user/tutorials/obsidian/obsidian_integration_guide',
            },
            {
              label: 'Docusaurus指南',
              to: '/user/tutorials/docusaurus/docusaurus_guide',
            },
          ],
        },
        {
          title: '社区',
          items: [
            {
              label: '讨论区',
              href: 'https://github.com/jacobcy/VibeCopilot/discussions',
            },
            {
              label: '问题反馈',
              href: 'https://github.com/jacobcy/VibeCopilot/issues',
            },
          ],
        },
        {
          title: '更多',
          items: [
            {
              label: '博客',
              to: '/blog',
            },
            {
              label: 'GitHub',
              href: 'https://github.com/jacobcy/VibeCopilot',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} VibeCopilot Project. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
