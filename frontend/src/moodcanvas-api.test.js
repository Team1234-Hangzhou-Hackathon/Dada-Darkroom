import assert from 'node:assert/strict';
import test from 'node:test';

import { checkApiHealth, createProcessFormData, mapGeneratedPaintings } from './moodcanvas-api.js';

test('maps available paintings returned by the MoodCanvas API', () => {
  const payload = {
    paintings: [
      { title: 'Opera', prompt: 'one', image_url: 'https://img.example/1.jpg' },
      { title: 'Desert', prompt: 'two', image_url: 'https://img.example/2.jpg' },
      { title: 'Ruins', prompt: 'three', image_url: 'https://img.example/3.jpg' },
      { title: 'Folded Room', prompt: 'four', image_url: 'https://img.example/4.jpg' },
      { title: 'Ritual', prompt: 'five', image_url: 'https://img.example/5.jpg' },
      { title: 'Failed', prompt: 'six', image_url: null },
    ],
  };

  const paintings = mapGeneratedPaintings(payload);

  assert.equal(paintings.length, 5);
  assert.deepEqual(paintings[0], {
    imageUrl: 'https://img.example/1.jpg',
    title: 'Opera',
    prompt: 'one',
  });
});

test('builds multipart request data for an uploaded image and description', () => {
  const sourceImage = new File(['photo'], 'reality.jpg', { type: 'image/jpeg' });

  const formData = createProcessFormData(sourceImage, '  焦虑，但又带一点荒诞  ');

  assert.equal(formData.get('image').name, 'reality.jpg');
  assert.equal(formData.get('text'), '焦虑，但又带一点荒诞');
});

test('checks whether the MoodCanvas backend is available', async () => {
  const requests = [];
  const available = await checkApiHealth(async (url) => {
    requests.push(url);
    return { ok: true };
  });

  assert.equal(available, true);
  assert.deepEqual(requests, ['/api/health']);
});
