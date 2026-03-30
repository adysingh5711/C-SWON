const fs = require('fs');
const path = require('path');

const dir = './components';
const files = fs.readdirSync(dir).filter(f => f.endsWith('.tsx') || f.endsWith('.ts'));

for (const f of files) {
  const fullPath = path.join(dir, f);
  const content = fs.readFileSync(fullPath, 'utf8');
  const newContent = content.replace(/\[--color-([a-zA-Z0-9-]+)\]/g, '$1').replace(/var\(--color-([a-zA-Z0-9-]+)\)/g, 'var(--$1)');
  fs.writeFileSync(fullPath, newContent);
}

console.log("Replacements complete.");
