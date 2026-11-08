// Persistent local instruct-model server for Prompt Fuzzer's `local` backend.
// Protocol: one JSON line {"system": ..., "user": ...} on stdin ->
// one line "MODEL_REPLY>>><reply>" on stdout. Zero cost, fully offline.
// Requires: npm install @huggingface/transformers (v3).
import { pipeline } from '@huggingface/transformers';
import readline from 'node:readline';

const model = process.argv[2] || 'onnx-community/Qwen2.5-0.5B-Instruct';
const gen = await pipeline('text-generation', model, { dtype: 'q4' });
console.error('MODEL_LOADED ' + model);

const rl = readline.createInterface({ input: process.stdin });
for await (const line of rl) {
  if (!line.trim()) continue;
  const { system, user } = JSON.parse(line);
  const out = await gen(
    [{ role: 'system', content: system }, { role: 'user', content: user }],
    { max_new_tokens: 120, do_sample: false });
  const reply = out[0].generated_text.at(-1).content.replace(/\n/g, ' ');
  console.log('MODEL_REPLY>>>' + reply);
}
