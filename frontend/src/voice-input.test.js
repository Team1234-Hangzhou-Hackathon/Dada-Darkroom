import assert from 'node:assert/strict';
import test from 'node:test';

import { appendRecognizedText, getSpeechRecognitionConstructor } from './voice-input.js';

test('appends final speech transcript without replacing typed mood text', () => {
  assert.equal(appendRecognizedText('压抑，但带一点戏谑', '  荒诞舞台  '), '压抑，但带一点戏谑 荒诞舞台');
  assert.equal(appendRecognizedText('', '  深夜办公室  '), '深夜办公室');
});

test('finds both standard and prefixed speech recognition constructors', () => {
  class StandardRecognition {}
  class EdgeRecognition {}

  assert.equal(
    getSpeechRecognitionConstructor({ SpeechRecognition: StandardRecognition }),
    StandardRecognition,
  );
  assert.equal(
    getSpeechRecognitionConstructor({ webkitSpeechRecognition: EdgeRecognition }),
    EdgeRecognition,
  );
  assert.equal(getSpeechRecognitionConstructor({}), null);
});
