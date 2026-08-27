// Menarik nomor HP/email/link medsos yang disebut di teks hasil pencarian
// (judul & cuplikan SerpApi) supaya bisa dipakai mengisi form input manual
// secara otomatis. Ini cuma bantuan pengisian - periset tetap wajib memeriksa
// & mengonfirmasi tiap kolom sebelum menyimpan (lihat ManualCandidateModal.vue).

const PHONE_REGEX = /(?:\+62|62|0)8\d{8,11}/;
const EMAIL_REGEX = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;

const SOCIAL_PATTERNS = [
  { key: "linkedin_url", regex: /(?:https?:\/\/)?(?:[\w-]+\.)?linkedin\.com\/(?:in|company)\/[a-zA-Z0-9_-]+\/?/i },
  { key: "instagram_url", regex: /(?:https?:\/\/)?(?:www\.)?instagram\.com\/[a-zA-Z0-9_.]+\/?/i },
  { key: "facebook_url", regex: /(?:https?:\/\/)?(?:www\.)?facebook\.com\/[a-zA-Z0-9.]+\/?/i },
  { key: "tiktok_url", regex: /(?:https?:\/\/)?(?:www\.)?tiktok\.com\/@[a-zA-Z0-9_.]+\/?/i },
];

const normalizeUrl = (match) => (match.startsWith("http") ? match : `https://${match}`);

export function parseContactInfo(text) {
  const found = {};
  if (!text) return found;

  const phoneMatch = text.match(PHONE_REGEX);
  if (phoneMatch) found.phone = phoneMatch[0];

  const emailMatch = text.match(EMAIL_REGEX);
  if (emailMatch) found.email = emailMatch[0];

  for (const { key, regex } of SOCIAL_PATTERNS) {
    const match = text.match(regex);
    if (match) found[key] = normalizeUrl(match[0]);
  }

  return found;
}
