export function appendRecognizedText(existingText, transcript) {
  const cleanTranscript = transcript.trim();
  const cleanExistingText = existingText.trimEnd();

  if (!cleanTranscript) {
    return existingText;
  }

  if (!cleanExistingText) {
    return cleanTranscript;
  }

  return `${cleanExistingText} ${cleanTranscript}`;
}

export function getSpeechRecognitionConstructor(browserWindow) {
  if (!browserWindow) {
    return null;
  }

  return browserWindow.SpeechRecognition || browserWindow.webkitSpeechRecognition || null;
}
