// Main assembler — combines all parts and writes DTI_Review_Paper.docx
import { Document, Packer } from 'docx';
import fs from 'fs';

import {
  titlePage, abstractSection, introSection, backgroundSection, mathSection
} from './generate_review_p1.mjs';

import { archSection, modelReviewSection } from './generate_review_p2.mjs';

import {
  tableSection, gapsSection, futureSection, conclusionSection, referenceSection
} from './generate_review_p3.mjs';

const allChildren = [
  ...titlePage,
  ...abstractSection,
  ...introSection,
  ...backgroundSection,
  ...mathSection,
  ...archSection,
  ...modelReviewSection,
  ...tableSection,
  ...gapsSection,
  ...futureSection,
  ...conclusionSection,
  ...referenceSection
];

const doc = new Document({
  sections: [{
    properties: {
      page: {
        margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 }
      }
    },
    children: allChildren
  }],
  styles: {
    default: {
      document: {
        run: { font: 'Times New Roman', size: 24 }
      }
    }
  }
});

const buffer = await Packer.toBuffer(doc);
fs.writeFileSync('DTI_Review_Paper.docx', buffer);
console.log(`Done. File: DTI_Review_Paper.docx (${(buffer.length / 1024).toFixed(1)} KB)`);
