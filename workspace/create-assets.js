const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const assetsDir = path.join(__dirname, 'assets');

// Color scheme
const colors = {
  deepNavy: '#0A1628',
  slateBlue: '#1E3A5F',
  techCyan: '#00D4FF',
  lightBlue: '#E8F4FD',
  white: '#FFFFFF',
  darkGray: '#2C3E50',
  accent: '#667EEA',
  accentLight: '#764BA2'
};

async function createGradient(filename, color1, color2, direction = 'vertical') {
  const width = 1440;
  const height = 810;

  let gradientDef;
  if (direction === 'vertical') {
    gradientDef = `<linearGradient id="g" x1="0%" y1="0%" x2="0%" y2="100%">`;
  } else if (direction === 'diagonal') {
    gradientDef = `<linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">`;
  } else {
    gradientDef = `<linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="0%">`;
  }

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
    <defs>
      ${gradientDef}
        <stop offset="0%" style="stop-color:${color1}"/>
        <stop offset="100%" style="stop-color:${color2}"/>
      </linearGradient>
    </defs>
    <rect width="100%" height="100%" fill="url(#g)"/>
  </svg>`;

  await sharp(Buffer.from(svg)).png().toFile(path.join(assetsDir, filename));
  console.log(`Created: ${filename}`);
}

async function createIcon(filename, svgContent, size = 64) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24">
    ${svgContent}
  </svg>`;

  await sharp(Buffer.from(svg)).png().toFile(path.join(assetsDir, filename));
  console.log(`Created: ${filename}`);
}

async function main() {
  // Create gradient backgrounds
  await createGradient('bg-dark.png', colors.deepNavy, colors.slateBlue, 'diagonal');
  await createGradient('bg-light.png', colors.lightBlue, colors.white, 'vertical');
  await createGradient('bg-accent.png', colors.accent, colors.accentLight, 'diagonal');

  // Create simple shape icons
  const iconColor = colors.techCyan;

  // Cost icon (dollar sign)
  await createIcon('icon-cost.png', `
    <circle cx="12" cy="12" r="10" fill="none" stroke="${iconColor}" stroke-width="1.5"/>
    <path d="M12 6v12M9 8.5c0 0 0-1 3-1s3 1 3 2.5-3 2-3 2 3 1 3 2.5-3 2.5-3 2.5" fill="none" stroke="${iconColor}" stroke-width="1.5"/>
  `, 80);

  // Efficiency icon (lightning)
  await createIcon('icon-efficiency.png', `
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" fill="none" stroke="${iconColor}" stroke-width="1.5" stroke-linejoin="round"/>
  `, 80);

  // Response icon (clock)
  await createIcon('icon-response.png', `
    <circle cx="12" cy="12" r="10" fill="none" stroke="${iconColor}" stroke-width="1.5"/>
    <polyline points="12 6 12 12 16 14" fill="none" stroke="${iconColor}" stroke-width="1.5"/>
  `, 80);

  // Brain icon for Agent
  await createIcon('icon-brain.png', `
    <path d="M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7z" fill="none" stroke="${iconColor}" stroke-width="1.5"/>
    <path d="M9 21h6M10 17v4M14 17v4" fill="none" stroke="${iconColor}" stroke-width="1.5"/>
  `, 80);

  // Gear icon for Skills
  await createIcon('icon-gear.png', `
    <circle cx="12" cy="12" r="3" fill="none" stroke="${iconColor}" stroke-width="1.5"/>
    <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" fill="none" stroke="${iconColor}" stroke-width="1.5"/>
  `, 80);

  // Database icon
  await createIcon('icon-database.png', `
    <ellipse cx="12" cy="5" rx="9" ry="3" fill="none" stroke="${iconColor}" stroke-width="1.5"/>
    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" fill="none" stroke="${iconColor}" stroke-width="1.5"/>
    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" fill="none" stroke="${iconColor}" stroke-width="1.5"/>
  `, 80);

  // Arrow right icon
  await createIcon('icon-arrow.png', `
    <line x1="5" y1="12" x2="19" y2="12" stroke="${iconColor}" stroke-width="2"/>
    <polyline points="12 5 19 12 12 19" fill="none" stroke="${iconColor}" stroke-width="2"/>
  `, 48);

  // Checkmark icon
  await createIcon('icon-check.png', `
    <polyline points="20 6 9 17 4 12" fill="none" stroke="#10B981" stroke-width="2.5"/>
  `, 48);

  console.log('All assets created successfully!');
}

main().catch(console.error);
