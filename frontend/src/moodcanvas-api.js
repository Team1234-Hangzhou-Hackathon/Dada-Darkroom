export function createProcessFormData(imageInput, description) {
  const formData = new FormData();
  formData.append('image', imageInput, imageInput.name || 'capture.jpg');
  formData.append('text', description.trim());
  return formData;
}

export function mapGeneratedPaintings(payload) {
  return (payload.paintings || [])
    .filter((painting) => Boolean(painting.image_url))
    .map((painting) => ({
      imageUrl: painting.image_url,
      title: painting.title,
      prompt: painting.prompt,
    }));
}

export async function checkApiHealth(request = fetch) {
  try {
    const response = await request('/api/health');
    return response.ok;
  } catch {
    return false;
  }
}

export async function generatePaintings(imageInput, description) {
  const response = await fetch('/api/process', {
    method: 'POST',
    body: createProcessFormData(imageInput, description),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || '生成图片失败，请确认后端服务已启动后重试。');
  }

  const paintings = mapGeneratedPaintings(await response.json());
  if (!paintings.length) {
    throw new Error('本次没有生成可展示的作品，请重试。');
  }

  return paintings;
}

export async function generateCreativeDesignFromUrl(imageUrl, description) {
  const imageResponse = await fetch(imageUrl);
  if (!imageResponse.ok) {
    throw new Error('读取选中图片失败，无法进入创意设计流程。');
  }

  const blob = await imageResponse.blob();
  const file = new File([blob], 'selected-painting.png', { type: blob.type || 'image/png' });
  const formData = new FormData();
  formData.append('image', file, file.name);
  formData.append('text', description.trim());

  const response = await fetch('/api/creative-design/auto', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || '创意设计流程失败，请确认后端服务已启动后重试。');
  }

  return response.json();
}
