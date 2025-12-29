const pptxgen = require('pptxgenjs');
const html2pptx = require('/Users/alexzhang/.claude/plugins/cache/anthropic-agent-skills/document-skills/c74d647e56e6/document-skills/pptx/scripts/html2pptx');
const path = require('path');

async function createPresentation() {
  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.author = 'Agent Skills Team';
  pptx.title = 'Agent Skills - 企业运营智能化转型';
  pptx.subject = '从人工运营到AI Agent驱动的智能运营新范式';

  const slidesDir = path.join(__dirname, 'slides');
  const slides = [
    'slide01-cover.html',
    'slide02-challenges.html',
    'slide03-vision.html',
    'slide04-architecture.html',
    'slide05-agent-layer.html',
    'slide06-skills-layer.html',
    'slide07-layer-interaction.html',
    'slide08-case-intro.html',
    'slide09-human-process.html',
    'slide10-arch-mapping.html',
    'slide11-workflow.html',
    'slide12-skills-matrix.html',
    'slide13-sequence.html',
    'slide14-tech-stack.html',
    'slide15-roadmap.html',
    'slide16-future.html',
    'slide17-summary.html'
  ];

  console.log('Generating presentation with', slides.length, 'slides...');

  for (let i = 0; i < slides.length; i++) {
    const slidePath = path.join(slidesDir, slides[i]);
    console.log(`Processing slide ${i + 1}/${slides.length}: ${slides[i]}`);
    try {
      await html2pptx(slidePath, pptx);
    } catch (err) {
      console.error(`Error processing ${slides[i]}:`, err.message);
      throw err;
    }
  }

  const outputPath = path.join(__dirname, 'agent_skills_enterprise.pptx');
  await pptx.writeFile({ fileName: outputPath });
  console.log('\nPresentation created successfully!');
  console.log('Output:', outputPath);
}

createPresentation().catch(err => {
  console.error('Failed to create presentation:', err);
  process.exit(1);
});
