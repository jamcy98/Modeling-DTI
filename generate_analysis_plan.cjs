const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  Table,
  TableRow,
  TableCell,
  WidthType,
  BorderStyle,
  AlignmentType,
  ShadingType,
  convertInchesToTwip,
  NumberFormat,
  LevelFormat,
  UnderlineType,
} = require("docx");
const fs = require("fs");
const path = require("path");

// ── Helpers ──────────────────────────────────────────────────────────────────

function heading1(text) {
  return new Paragraph({
    text,
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 160 },
  });
}

function heading2(text) {
  return new Paragraph({
    text,
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 320, after: 120 },
  });
}

function heading3(text) {
  return new Paragraph({
    text,
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 240, after: 80 },
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    children: [
      new TextRun({
        text,
        size: 24, // 12pt
        font: "Calibri",
        ...opts,
      }),
    ],
    spacing: { after: 120, line: 276 },
    alignment: AlignmentType.JUSTIFIED,
  });
}

function bullet(text, level = 0) {
  return new Paragraph({
    children: [new TextRun({ text, size: 24, font: "Calibri" })],
    bullet: { level },
    spacing: { after: 80, line: 276 },
    indent: { left: convertInchesToTwip(0.25 * (level + 1)) },
  });
}

function numbered(text, level = 0) {
  return new Paragraph({
    children: [new TextRun({ text, size: 24, font: "Calibri" })],
    numbering: { reference: "default-numbering", level },
    spacing: { after: 80, line: 276 },
  });
}

function spacer() {
  return new Paragraph({ text: "", spacing: { after: 80 } });
}

function boldBody(label, rest = "") {
  return new Paragraph({
    children: [
      new TextRun({ text: label, bold: true, size: 24, font: "Calibri" }),
      new TextRun({ text: rest, size: 24, font: "Calibri" }),
    ],
    spacing: { after: 100, line: 276 },
  });
}

// ── Table builder ────────────────────────────────────────────────────────────

function makeTable(headers, rows, colWidths) {
  const headerCells = headers.map((h, i) =>
    new TableCell({
      children: [
        new Paragraph({
          children: [new TextRun({ text: h, bold: true, size: 22, font: "Calibri" })],
          alignment: AlignmentType.CENTER,
        }),
      ],
      width: { size: colWidths[i], type: WidthType.PERCENTAGE },
      shading: { type: ShadingType.CLEAR, fill: "1F497D" },
    })
  );

  const tableRows = [
    new TableRow({ children: headerCells, tableHeader: true }),
    ...rows.map((row, ri) =>
      new TableRow({
        children: row.map((cell, ci) =>
          new TableCell({
            children: [
              new Paragraph({
                children: [new TextRun({ text: cell, size: 22, font: "Calibri" })],
              }),
            ],
            width: { size: colWidths[ci], type: WidthType.PERCENTAGE },
            shading: {
              type: ShadingType.CLEAR,
              fill: ri % 2 === 0 ? "FFFFFF" : "EBF3F9",
            },
          })
        ),
      })
    ),
  ];

  return new Table({
    rows: tableRows,
    width: { size: 100, type: WidthType.PERCENTAGE },
  });
}

// ── Document ─────────────────────────────────────────────────────────────────

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "default-numbering",
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.LEFT,
          },
        ],
      },
    ],
  },
  styles: {
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        run: { size: 32, bold: true, color: "1F497D", font: "Calibri Light" },
        paragraph: { spacing: { before: 400, after: 160 } },
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        run: { size: 28, bold: true, color: "2E74B5", font: "Calibri Light" },
        paragraph: { spacing: { before: 320, after: 120 } },
      },
      {
        id: "Heading3",
        name: "Heading 3",
        basedOn: "Normal",
        next: "Normal",
        run: { size: 26, bold: true, color: "5B9BD5", font: "Calibri Light" },
        paragraph: { spacing: { before: 240, after: 80 } },
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          margin: {
            top: convertInchesToTwip(1),
            right: convertInchesToTwip(1),
            bottom: convertInchesToTwip(1),
            left: convertInchesToTwip(1.25),
          },
        },
      },
      children: [
        // ── Title page block ────────────────────────────────────────────────
        new Paragraph({
          children: [
            new TextRun({
              text: "Analysis Plan for Objective 1",
              bold: true,
              size: 40,
              font: "Calibri Light",
              color: "1F497D",
            }),
          ],
          alignment: AlignmentType.CENTER,
          spacing: { before: 600, after: 200 },
        }),
        new Paragraph({
          children: [
            new TextRun({
              text: "H-GNN-RNN-DTI Research Project",
              size: 28,
              font: "Calibri",
              color: "595959",
            }),
          ],
          alignment: AlignmentType.CENTER,
          spacing: { after: 120 },
        }),
        new Paragraph({
          children: [
            new TextRun({
              text: "Universiti Sains Malaysia  |  School of Computer Sciences  |  2025",
              size: 22,
              font: "Calibri",
              color: "808080",
            }),
          ],
          alignment: AlignmentType.CENTER,
          spacing: { after: 800 },
        }),

        // ── Objective Statement ─────────────────────────────────────────────
        heading1("Objective 1 — What We Are Trying to Do"),
        body(
          "The goal of Objective 1 is to build and test an improved deep learning model called H-GNN-RNN-DTI. " +
          "This model will learn from two different types of biological data at the same time — the " +
          "3D structure of a drug molecule and the amino acid sequence of a protein target. " +
          "It will then combine what it learns from both sources using a smart mixing layer called " +
          "the Gated Cross-Attention mechanism."
        ),
        body(
          "At the end, the model must perform better — and show that the improvement is statistically " +
          "significant — compared to older models that simply stick the two data types together without " +
          "any intelligent mixing."
        ),
        spacer(),

        // ── Overview ────────────────────────────────────────────────────────
        heading1("Overview of the Analysis Plan"),
        body(
          "The plan is divided into five phases. Each phase must be completed before moving to the next one."
        ),
        makeTable(
          ["Phase", "What Happens", "Main Output"],
          [
            ["1 — Data Gathering", "Download all datasets needed for training and testing.", "Raw dataset files"],
            ["2 — Data Preprocessing", "Clean and convert the raw data into a format the model can read.", "Ready-to-use data files"],
            ["3 — Baseline Setup", "Reproduce the results of three existing models for fair comparison.", "Baseline performance numbers"],
            ["4 — Model Building", "Build the H-GNN-RNN-DTI model step by step.", "Trained model"],
            ["5 — Evaluation", "Test the model and compare it to the baselines.", "Results tables and charts"],
          ],
          [10, 55, 35]
        ),
        spacer(),

        // ── Phase 1 ─────────────────────────────────────────────────────────
        heading1("Phase 1: Data Gathering"),
        body(
          "We need several publicly available datasets. Each dataset provides a list of drug–protein pairs " +
          "along with a label that says whether the drug and protein interact (yes/no) or how strongly " +
          "they bind (a number called the binding affinity)."
        ),

        heading2("1.1  Which Datasets to Download"),
        makeTable(
          ["Dataset", "Task Type", "Why We Need It", "Priority"],
          [
            ["DAVIS", "Affinity (regression)", "Gold-standard dataset with measured Kd values. Widely used to test regression models.", "High"],
            ["KIBA", "Affinity (regression)", "Complements DAVIS. Combines multiple affinity measures into one score.", "High"],
            ["Yamanishi_08", "Interaction (yes/no)", "Small, well-curated dataset. Needed to reproduce the DTKGIN baseline result.", "High"],
            ["Luo_17", "Interaction (yes/no)", "Larger network-based dataset. Needed to reproduce the GSRF-DTI baseline result.", "High"],
            ["BindingDB", "Both tasks", "Very large database with real experimental binding data for many drug–protein pairs.", "High"],
            ["ChEMBL", "Both tasks", "Used later to test how well the trained model works on completely new data.", "Medium"],
            ["DrugBank", "Supplementary", "Used to pre-train the model before the main training starts.", "Medium"],
          ],
          [15, 18, 47, 10]
        ),
        spacer(),

        heading2("1.2  What to Download for Each Dataset"),
        body("For every dataset, you need three things:"),
        bullet("Interaction labels — a file that maps each drug–protein pair to a label (1 = interact, 0 = do not interact) or an affinity number."),
        bullet("Drug SMILES strings — a text representation of each drug's chemical structure (e.g., CCO for ethanol)."),
        bullet("Protein FASTA sequences — the amino acid sequence of each protein target (e.g., MKTAYIAKQ...)."),
        spacer(),

        heading2("1.3  Step-by-Step Download Instructions"),

        heading3("Step 1 — DAVIS and KIBA"),
        body(
          "Clone the DeepDTA GitHub repository. It contains ready-made files for both datasets. " +
          "This is the safest option because many published papers used these exact files, making " +
          "comparisons fair."
        ),
        bullet("Files needed: affinity matrix (Y), ligands file (SMILES), proteins file (sequences)"),

        heading3("Step 2 — Yamanishi_08 and Luo_17"),
        body(
          "Download from the DTINet GitHub repository or from the supplementary material of the " +
          "Luo et al. (2017) paper. The Yamanishi_08 dataset has four sub-groups: " +
          "Enzyme (E), Ion Channel (IC), GPCR, and Nuclear Receptor (NR)."
        ),
        bullet("Download all four sub-groups from Yamanishi_08 separately."),
        bullet("Download the full Luo_17 drug–target interaction matrix."),

        heading3("Step 3 — BindingDB"),
        body(
          "Go to the BindingDB website and download the full file: BindingDB_All.tsv.gz. " +
          "After downloading, apply these filters to keep only useful records:"
        ),
        bullet("Keep only rows with Kd, Ki, or IC50 values."),
        bullet("Remove rows with missing SMILES or missing UniProt protein ID."),
        bullet("For binary labelling: mark as positive (1) if Kd ≤ 10,000 nM; mark as negative (0) otherwise."),

        heading3("Step 4 — ChEMBL (for transfer testing)"),
        body(
          "Download the ChEMBL SQLite database from the ChEMBL website, or use their REST API. " +
          "Filter records to keep only those where:"
        ),
        bullet("Measurement type is IC50, Ki, or Kd"),
        bullet("Measurement relation is '=' (exact value, not '>=' or '<')"),
        bullet("Units are nM"),
        bullet("pChEMBL value is available"),

        heading3("Step 5 — DrugBank (for pre-training)"),
        body(
          "Register for a free academic account at drugbank.ca. Then download:"
        ),
        bullet("drugbank_all_structures.sdf — contains SMILES for all drugs"),
        bullet("drug_target_links.csv — contains known drug–protein interaction pairs"),
        spacer(),

        heading2("1.4  Data Quality Checks"),
        body(
          "Before moving to preprocessing, check the data quality. The table below lists what to " +
          "check and what to do if there is a problem."
        ),
        makeTable(
          ["What to Check", "How to Fix It"],
          [
            ["Duplicate drug–protein pairs", "Remove duplicates. If two rows have the same pair but different affinity values, keep the one with the smaller (more precise) value."],
            ["Invalid SMILES strings", "Use RDKit to check each SMILES. Remove any that RDKit cannot read. Record how many were removed."],
            ["Missing protein sequences", "Use the UniProt REST API to look up missing sequences by their accession number."],
            ["Very unusual affinity values (pKd < 3 or > 12)", "Flag these rows. Consider removing them or capping the values."],
            ["How many positives vs. negatives", "Count the ratio. Write it down — you will need it to set the negative sampling ratio in Phase 2."],
            ["How long the protein sequences are", "Find the 95th percentile length. Use this as your maximum sequence length when padding/truncating."],
          ],
          [35, 65]
        ),
        spacer(),

        // ── Phase 2 ─────────────────────────────────────────────────────────
        heading1("Phase 2: Data Preprocessing"),
        body(
          "Raw data cannot be fed directly into the model. We need to convert drugs into graphs " +
          "and proteins into number vectors (embeddings)."
        ),

        heading2("2.1  Drug Representation — Building a Molecular Graph"),
        body("For each drug SMILES string, do the following:"),
        numbered("Use RDKit (a Python chemistry library) to read the SMILES and build a molecular graph."),
        numbered("Each atom becomes a node. The node features are: atomic number, number of bonds (degree), type of hybridization (sp, sp2, sp3), whether the atom is aromatic (yes/no), and formal charge."),
        numbered("Each bond becomes an edge. The edge features are: bond type (single, double, triple, aromatic), whether it is conjugated (yes/no), and whether it is in a ring (yes/no)."),
        numbered("Add pre-trained ChemBERTa embeddings as extra node features. ChemBERTa is a language model trained on millions of drug molecules. Its embeddings give the model extra chemical knowledge at the start."),
        spacer(),

        heading2("2.2  Protein Representation — Building a Sequence Embedding"),
        body("For each protein FASTA sequence, do the following:"),
        numbered("Feed the sequence into the pre-trained ESM-2 model (650 million parameter version). ESM-2 was trained on hundreds of millions of protein sequences and understands how amino acids relate to each other."),
        numbered("ESM-2 outputs a vector (a list of numbers) for each amino acid residue in the sequence. These are called residue-level embeddings."),
        numbered("Pad sequences shorter than the maximum length with zeros. Cut sequences longer than the maximum length at the end. The maximum length is the 95th percentile length found in Step 1.4."),
        spacer(),

        heading2("2.3  Label Preparation"),
        boldBody("For binary classification (DTI): "),
        bullet("Verified known interactions = label 1 (positive)"),
        bullet("Unknown or non-interacting pairs = label 0 (negative)"),
        bullet("Use negative sampling. Generate 1 negative pair for every 1 positive pair (1:1 ratio) as the default. Also prepare a 1:10 version to test how the model handles extreme imbalance."),
        spacer(),
        boldBody("For affinity regression (DTA): "),
        bullet("Convert raw Kd/Ki/IC50 values using the formula: pValue = −log10(value in Molar)"),
        bullet("This turns large numbers like 1,000,000 nM into small ones like 3.0. It makes training more stable."),
        spacer(),

        heading2("2.4  Data Splitting"),
        body("We will split the data in four different ways to test the model fairly."),
        makeTable(
          ["Split Name", "How It Works", "What It Tests"],
          [
            ["Random split (10-fold cross-validation)", "Randomly divide all pairs into 10 equal groups. Train on 9 groups, test on 1. Repeat 10 times.", "General model performance under normal conditions."],
            ["Cold-drug split", "Put all pairs involving certain drugs into the test set only. The model never sees these drugs during training.", "Can the model predict interactions for brand-new drug compounds?"],
            ["Cold-target split", "Put all pairs involving certain proteins into the test set only. The model never sees these proteins during training.", "Can the model predict interactions for brand-new protein targets?"],
            ["Cross-dataset split", "Train on one dataset (e.g., BindingDB). Test on a completely different dataset (e.g., DAVIS).", "Does the model generalise across different experimental conditions?"],
          ],
          [22, 43, 35]
        ),
        spacer(),

        // ── Phase 3 ─────────────────────────────────────────────────────────
        heading1("Phase 3: Baseline Setup"),
        body(
          "Before testing our new model, we must first reproduce the published results of three existing models. " +
          "This ensures the comparison is honest and that our evaluation setup is correct."
        ),

        heading2("3.1  Baselines to Reproduce"),
        makeTable(
          ["Baseline Model", "Dataset", "Target Score to Match"],
          [
            ["GSRF-DTI (Zhu et al., 2024)", "Luo_17", "AUROC = 0.9818, AUPR = 0.9839"],
            ["DTKGIN (Luo et al., 2024)", "Yamanishi_08 — cold-drug setting (S2)", "AUC = 0.894, AUPR = 0.753"],
            ["Simple Concatenation GNN-RNN", "Same datasets as above", "This is our own simplified version — records initial score before adding cross-attention."],
          ],
          [30, 30, 40]
        ),
        spacer(),
        body(
          "The third baseline — the Simple Concatenation GNN-RNN — is the most important one for " +
          "Objective 1. It is the same as our model but without the Gated Cross-Attention fusion. " +
          "The difference in performance between this baseline and the full model is what proves " +
          "that the cross-attention layer helps."
        ),
        spacer(),

        // ── Phase 4 ─────────────────────────────────────────────────────────
        heading1("Phase 4: Building the H-GNN-RNN-DTI Model"),
        body(
          "The model has three main parts. Each part is built and tested separately before they are " +
          "all connected together."
        ),

        heading2("4.1  Drug Encoder (Graph Attention Network)"),
        body("This part reads the drug molecular graph and produces a single vector that summarises the drug."),
        bullet("Use a Graph Attention Network (GAT) with 3 layers and 8 attention heads per layer."),
        bullet("In each layer, every atom collects information from its neighbouring atoms. Atoms that are more important get higher attention weights."),
        bullet("After the last layer, combine all atom vectors into one drug-level vector using an attention-based READOUT step, followed by a small MLP (multi-layer perceptron)."),
        spacer(),

        heading2("4.2  Protein Encoder (Bidirectional RNN)"),
        body("This part reads the protein sequence and produces a single vector that summarises the protein."),
        bullet("Use a Bidirectional LSTM or Bidirectional GRU with 2 layers."),
        bullet("'Bidirectional' means the model reads the sequence left-to-right AND right-to-left at the same time, so it understands context from both directions."),
        bullet("After processing, combine all residue-level vectors into one protein-level vector using attention-based pooling."),
        spacer(),

        heading2("4.3  Gated Cross-Attention Fusion"),
        body("This is the most important and novel part of the model."),
        bullet("The drug and protein vectors are combined here — but not by simple joining."),
        bullet("Instead, the drug vector 'looks at' the protein vector to find which parts of the protein are most relevant to that drug, and vice versa. This is the cross-attention step."),
        bullet("A gate (a sigmoid function) then controls how much of this cross-attention information flows through. This prevents too much noise from distorting the drug or protein representation."),
        bullet("The result is one combined drug–protein vector that captures the interaction between the two."),
        spacer(),

        heading2("4.4  Prediction Head"),
        body("The final step maps the combined drug–protein vector to a prediction."),
        bullet("For binary classification (does the drug interact with the protein?): the MLP ends with a sigmoid activation → outputs a probability between 0 and 1."),
        bullet("For affinity regression (how strongly do they bind?): the MLP ends with a linear activation → outputs a continuous number like pKd."),
        spacer(),

        // ── Phase 5 ─────────────────────────────────────────────────────────
        heading1("Phase 5: Training and Evaluation"),

        heading2("5.1  Training Setup"),
        makeTable(
          ["Setting", "Choice", "Reason"],
          [
            ["Loss function (classification)", "Focal Loss", "Handles class imbalance. Makes the model focus on hard-to-predict examples."],
            ["Loss function (regression)", "Mean Squared Error (MSE)", "Standard choice for predicting continuous values."],
            ["Optimizer", "Adam with weight decay", "Fast and stable. Weight decay prevents overfitting."],
            ["Learning rate schedule", "Reduce on plateau + early stopping", "Stops training automatically when the model stops improving."],
            ["Regularization", "Dropout layers", "Randomly turns off some neurons during training to prevent the model from memorising the data."],
          ],
          [25, 30, 45]
        ),
        spacer(),

        heading2("5.2  Ablation Study"),
        body(
          "To prove that each part of the model helps, we will train several simplified versions and " +
          "compare them to the full model."
        ),
        makeTable(
          ["Model Version", "What Is Missing", "What We Learn"],
          [
            ["GNN only", "No protein encoder, no fusion", "How much does the drug structure alone contribute?"],
            ["RNN only", "No drug encoder, no fusion", "How much does the protein sequence alone contribute?"],
            ["GNN + RNN with concatenation", "No cross-attention fusion", "This is the direct test of Objective 1 — does cross-attention beat simple concatenation?"],
            ["Full H-GNN-RNN-DTI", "Nothing removed — complete model", "Best performance expected."],
          ],
          [30, 35, 35]
        ),
        spacer(),

        heading2("5.3  Performance Metrics"),
        boldBody("For binary interaction classification:"),
        bullet("AUC-ROC — Area under the Receiver Operating Characteristic curve. Higher is better. Maximum = 1.0."),
        bullet("AUPR — Area under the Precision–Recall curve. More informative than AUC when the dataset is imbalanced."),
        spacer(),
        boldBody("For binding affinity regression:"),
        bullet("RMSE — Root Mean Squared Error. Measures the average prediction error. Lower is better."),
        bullet("MAE — Mean Absolute Error. Similar to RMSE but less sensitive to large errors."),
        bullet("PCC — Pearson Correlation Coefficient. Measures how closely the predicted values match the real values. Higher is better. Maximum = 1.0."),
        spacer(),

        heading2("5.4  Statistical Testing"),
        body(
          "To claim that our model is better than the baselines, we must show the difference is " +
          "statistically significant — not just luck. We will:"
        ),
        bullet("Run each experiment with at least 5 different random seeds."),
        bullet("Report the mean score ± standard deviation across all runs."),
        bullet("Use a paired t-test or Wilcoxon signed-rank test to compare our model to each baseline."),
        bullet("A result is considered significant if the p-value is less than 0.05."),
        spacer(),

        // ── Deliverables ─────────────────────────────────────────────────────
        heading1("Deliverables for Objective 1"),
        body("By the end of this phase of the research, the following items must be ready:"),
        makeTable(
          ["#", "Deliverable", "Description"],
          [
            ["1", "Cleaned dataset files", "All datasets downloaded, filtered, and saved in a consistent format with clear version numbers."],
            ["2", "Preprocessing scripts", "Python code using RDKit and ESM-2 to convert raw data into drug graphs and protein embeddings. Must be reusable."],
            ["3", "Baseline results", "Reproduced performance numbers for GSRF-DTI, DTKGIN, and the simple concatenation model."],
            ["4", "Trained H-GNN-RNN-DTI model", "The fully trained model, including the saved weights file and training logs."],
            ["5", "Ablation study results", "A table comparing all model variants (GNN-only, RNN-only, concatenation, full model)."],
            ["6", "Evaluation report", "A summary table of all metrics across all datasets and split types, with statistical significance noted."],
          ],
          [5, 28, 67]
        ),
        spacer(),

        // ── First Action ─────────────────────────────────────────────────────
        heading1("Where to Start First"),
        body(
          "Begin with the DAVIS and Yamanishi_08 datasets because they are small and well-structured. " +
          "This lets you build and test the entire pipeline — from download to model training — quickly. " +
          "Once the pipeline works on small data, it is easy to add the larger datasets."
        ),
        spacer(),
        makeTable(
          ["Week", "Task"],
          [
            ["Week 1–2", "Download DAVIS, KIBA, Yamanishi_08, and Luo_17. Run data quality checks."],
            ["Week 3–4", "Write preprocessing scripts. Build drug graphs and protein embeddings for DAVIS and Yamanishi_08."],
            ["Week 5–6", "Reproduce DTKGIN and GSRF-DTI baselines. Build the simple concatenation model."],
            ["Week 7–10", "Build and train the full H-GNN-RNN-DTI model. Run ablation studies."],
            ["Week 11–12", "Run all evaluations. Write up results. Download and test on BindingDB and ChEMBL."],
          ],
          [15, 85]
        ),
        spacer(),
      ],
    },
  ],
});

const outputPath = path.join(__dirname, "Proposal", "Objective1_Analysis_Plan.docx");

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(outputPath, buffer);
  console.log("Done! File saved to:", outputPath);
});
