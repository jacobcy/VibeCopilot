// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const {themes} = require('prism-react-renderer');
const lightCodeTheme = themes.github;
const darkCodeTheme = themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'VibeCopilot 文档',
  tagline: '一站式文档解决方案',
  favicon: 'img/favicon.ico',

  // 设置网站URL
  url: 'https://your-docusaurus-site.example.com',
  baseUrl: '/',

  // GitHub pages部署配置
  organizationName: 'vibecopilot',
  projectName: 'vibecopilot-docs',

  onBrokenLinks: 'warn',
  onBrokenAnchors: 'warn',
  onBrokenMarkdownLinks: 'warn',

  // 国际化配置
  i18n: {
    defaultLocale: 'zh-CN',
    locales: ['zh-CN', 'en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          // 编辑链接
          editUrl:
            'https://github.com/vibecopilot/vibecopilot/tree/main/website/',
        },
        blog: {
          showReadingTime: true,
          // 编辑链接
          editUrl:
            'https://github.com/vibecopilot/vibecopilot/tree/main/website/',
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // 替换为你的项目logo
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
          {to: '/blog', label: '博客', position: 'left'},
          {
            href: 'https://github.com/vibecopilot/vibecopilot',
            label: 'GitHub',
            position: 'right',
          },
          {
            type: 'localeDropdown',
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
                label: '教程',
                to: '/docs/intro',
              },
            ],
          },
          {
            title: '社区',
            items: [
              {
                label: 'Discord',
                href: 'https://discord.gg/docusaurus',
              },
              {
                label: 'Twitter',
                href: 'https://twitter.com/docusaurus',
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
                href: 'https://github.com/vibecopilot/vibecopilot',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} VibeCopilot. Built with Docusaurus.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        additionalLanguages: ['bash', 'diff', 'json', 'python'],
      },
    }),
};

module.exports = config;
