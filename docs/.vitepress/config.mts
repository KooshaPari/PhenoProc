import { defineConfig } from "vitepress";

export default defineConfig({
  title: "PhenoProc",
  description: "Process orchestration and workflow management for Phenotype",
  base: "/PhenoProc/",
  themeConfig: {
    nav: [
      { text: "Home", link: "/" },
      { text: "Guide", link: "/guide/" },
      { text: "Reference", link: "/reference/" },
      { text: "Research", link: "/research/" },
    ],
    sidebar: {
      "/guide/": [
        {
          text: "Guide",
          items: [
            { text: "Overview", link: "/guide/" },
            { text: "Getting started", link: "/guide/getting-started" },
          ],
        },
      ],
      "/reference/": [
        {
          text: "Reference",
          items: [
            { text: "Reference", link: "/reference/" },
            { text: "ADR", link: "/ADR" },
          ],
        },
      ],
    },
  },
});
