const fs = require('fs');
const postcss = require('postcss');
const tailwindPostcss = require('@tailwindcss/postcss');
const autoprefixer = require('autoprefixer');

const inputPath = './static/input.css';
const outputPath = './static/output.css';

async function build() {
  try {
    const css = fs.readFileSync(inputPath, 'utf8');
    const result = await postcss([tailwindPostcss({ config: './tailwind.config.js' }), autoprefixer]).process(css, {
      from: inputPath,
      to: outputPath,
      map: false,
    });
    fs.writeFileSync(outputPath, result.css);
    console.log('Built', outputPath);
  } catch (err) {
    console.error('Build failed:', err);
    process.exitCode = 1;
  }
}

build();
