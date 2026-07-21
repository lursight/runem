/** @type {import("prettier").Config} */
module.exports = {
  overrides: [
    {
      files: ["*.md", "*.mdx"],
      options: {
        // Do not load additional plugins implicitly.
        plugins: [],
        // Keep trailing commas in ES5-compatible locations.
        trailingComma: "es5",
        // Wrap Markdown prose rather than preserving source lines.
        proseWrap: "always",
        // Markdown lines wrap at 88 columns.
        printWidth: 88,
        // Markdown indentation uses two spaces.
        tabWidth: 2,
        // Print semicolons at the ends of statements in embedded code.
        semi: true,
        // Use spaces instead of tab characters for indentation.
        useTabs: false,
        // Use double quotes in embedded JavaScript.
        singleQuote: false,
        // Use double quotes in JSX attributes.
        jsxSingleQuote: false,
        // Always include parentheses around a single arrow-function parameter.
        arrowParens: "always",
        // Add spaces inside object literals and similar braces.
        bracketSpacing: true,
        // Put the `>` of multiline JSX elements on the last line.
        bracketSameLine: false,
        // Use LF line endings.
        endOfLine: "lf",
        // Respect CSS whitespace sensitivity when formatting embedded HTML.
        htmlWhitespaceSensitivity: "css",
        // Format embedded code when Prettier can identify its language.
        embeddedLanguageFormatting: "auto",
        // Format files without requiring a `@prettier` pragma.
        requirePragma: false,
        // Do not insert a `@format` pragma into formatted files.
        insertPragma: false,
        // Do not force a separate line for each HTML-like attribute.
        singleAttributePerLine: false,
        // Do not alter indentation inside Vue <script> and <style> blocks.
        vueIndentScriptAndStyle: false,
      },
    },
  ],
};
