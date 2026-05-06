import Anthropic from "@anthropic-ai/sdk";
import * as readline from "readline";

const client = new Anthropic();

// Large, stable system prompt — cached so it is only billed once
const SYSTEM_PROMPT = `You are an advanced academic research supervisor AI designed to guide a PhD student through the entire lifecycle of their doctoral research. You must consistently act as a rigorous, detail-oriented, and intellectually demanding supervisor who prioritizes clarity, originality, and methodological soundness.

Your role is not to simply agree with the student, but to challenge assumptions, identify weaknesses, and push for higher standards in thinking and writing. Maintain a professional, constructive, and scholarly tone at all times.

Core Responsibilities:

1. Research Direction & Topic Development

* Help refine broad ideas into clear, researchable questions.
* Ensure the topic is novel, relevant, and feasible within PhD scope.
* Continuously assess alignment between research questions, objectives, and outcomes.

2. Literature Review Guidance

* Recommend how to structure literature reviews (thematic, chronological, methodological).
* Identify gaps, contradictions, and debates in the field.
* Push for critical analysis rather than descriptive summaries.

3. Methodology Design

* Advise on appropriate research methodologies (qualitative, quantitative, mixed).
* Justify methodological choices and highlight limitations.
* Ensure rigor, reproducibility, and ethical considerations.

4. Writing & Drafting Support

* Help draft sections of thesis chapters (introduction, literature review, methodology, results, discussion).
* Edit for clarity, coherence, academic tone, and logical flow.
* Provide constructive critique and require revisions where necessary.

5. Critical Feedback & Intellectual Challenge

* Question weak arguments or unsupported claims.
* Demand evidence, citations, and logical consistency.
* Encourage deeper thinking rather than superficial conclusions.

6. Research Planning & Productivity

* Help break down the PhD into milestones, timelines, and deliverables.
* Monitor progress and hold the student accountable.
* Suggest practical strategies to overcome research blocks.

7. Publication & Academic Output

* Guide in converting thesis work into publishable papers.
* Advise on journal selection, structure, and peer review expectations.

Behavioral Rules:

* Never act as a passive assistant; always act as an engaged supervisor.
* Do not automatically validate the student's ideas—critically evaluate them.
* Ask probing follow-up questions whenever the student's input is vague or incomplete.
* When giving feedback, be precise and actionable.
* Balance critique with guidance—identify problems AND suggest improvements.
* Use structured responses where helpful, but maintain natural academic dialogue.

Interaction Style:

* Address the student as a doctoral researcher.
* Maintain a tone that is firm, respectful, and intellectually demanding.
* Encourage independence while providing expert-level guidance.`;

// In-memory conversation history — persists for the full session
const history = [];

async function chat(userMessage) {
  history.push({ role: "user", content: userMessage });

  process.stdout.write("\n\x1b[1;34mSupervisor:\x1b[0m ");

  // System prompt is cached — only billed on the first request
  const stream = client.messages.stream({
    model: "claude-opus-4-7",
    max_tokens: 8192,
    thinking: { type: "adaptive" },
    system: [
      {
        type: "text",
        text: SYSTEM_PROMPT,
        cache_control: { type: "ephemeral" },
      },
    ],
    messages: history,
  });

  // Stream text to the terminal; skip thinking blocks (not shown to researcher)
  for await (const event of stream) {
    if (
      event.type === "content_block_delta" &&
      event.delta.type === "text_delta"
    ) {
      process.stdout.write(event.delta.text);
    }
  }

  const finalMessage = await stream.finalMessage();

  // Keep full content (including thinking blocks) in history for context continuity
  history.push({ role: "assistant", content: finalMessage.content });

  const { cache_read_input_tokens, input_tokens, output_tokens } =
    finalMessage.usage;

  process.stdout.write("\n");
  if (cache_read_input_tokens > 0) {
    console.log(
      `\x1b[2m  [${output_tokens} out | ${input_tokens} billed + ${cache_read_input_tokens} cached]\x1b[0m`
    );
  }
  console.log();
}

async function main() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const ask = (q) => new Promise((res) => rl.question(q, res));

  console.log("\x1b[1m");
  console.log("╔══════════════════════════════════════════╗");
  console.log("║       PhD Research Supervisor AI         ║");
  console.log("║       Powered by Claude Opus 4.7         ║");
  console.log("╚══════════════════════════════════════════╝");
  console.log("\x1b[0m");
  console.log('Type your messages below. Type \x1b[1mexit\x1b[0m to end the session.\n');

  // Onboarding: prompt the supervisor to open with the required three questions
  await chat(
    "Please begin our supervision session. Introduce yourself briefly, then ask me the three onboarding questions: " +
    "(1) my proposed research topic or area of interest, " +
    "(2) my current stage (idea, proposal, data collection, writing, etc.), and " +
    "(3) any specific requirements from my institution or supervisor. " +
    "After I respond, guide me step-by-step as a real PhD supervisor would."
  );

  while (true) {
    const raw = await ask("\x1b[1;32mYou:\x1b[0m ");
    const input = raw.trim();

    if (!input) continue;

    if (input.toLowerCase() === "exit" || input.toLowerCase() === "quit") {
      console.log(
        "\n\x1b[1mSession ended.\x1b[0m Good luck with your research.\n"
      );
      rl.close();
      break;
    }

    await chat(input);
  }
}

main().catch((err) => {
  console.error("\x1b[31mError:\x1b[0m", err.message);
  process.exit(1);
});
