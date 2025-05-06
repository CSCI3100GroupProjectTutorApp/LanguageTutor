import { Word, WordCreate, WordUpdate } from '../../assets/types/Word';
import { getAuthToken } from '../services/authService'

const API_BASE_URL = 'http://192.168.0.118:8000';

// Interface for the translation API response
interface TranslationResponse {
  word: string;
  translated_word: string;
  part_of_speech: string[];
  english_meanings: string[][];
  source_language: string;
  target_language: string;
}

const mapPartOfSpeech = (abbr: string): string => {
  switch (abbr.toLowerCase()) {
    case 'n':
      return 'Noun';
    case 'v':
      return 'Verb';
    case 'a':
    case 's': // Per request, mark "s" as adjective as well
      return 'Adjective';
    case 'r':
      return 'Adverb';
    default:
      return abbr; // Return original if not recognized
  }
};

/**
 * Translates a word and formats it as a WordCreate object
 * If the word contains both "s" and "a", take at most 2 meanings from each (up to 4 total)
 * Otherwise get at most 3 English meanings for each part of speech
 */
export const translateWordCreate = async (word: string): Promise<WordCreate> => {
  try {
    const token = await getAuthToken();
    if (!token) {
        throw new Error('Not authenticated');
    }
    // Call the translation API
    const response = await fetch(`${API_BASE_URL}/translate/word`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        word: word,
        target_language: 'zh-tw'
      })
    });

    if (!response.ok) {
      throw new Error(`Translation failed with status: ${response.status}`);
    }

    const data: TranslationResponse = await response.json();
    
    // Check if the word contains both "s" and "a" part of speech types
    const aPosIndex = data.part_of_speech.indexOf('a');
    const sPosIndex = data.part_of_speech.indexOf('s');
    const hasBothSAndA = aPosIndex !== -1 && sPosIndex !== -1;
    
    // Convert abbreviated parts of speech to full forms
    const normalizedPOS = data.part_of_speech.map(mapPartOfSpeech);
    
    // Group the English meanings by their normalized parts of speech
    const groupedMeanings: { [key: string]: string[] } = {};
    
    // Special handling for 's' and 'a' (both adjectives)
    if (hasBothSAndA) {
      // Get at most 2 meanings from each 's' and 'a'
      const aMeanings = (data.english_meanings[aPosIndex] || []).slice(0, 3);
      const sMeanings = (data.english_meanings[sPosIndex] || []).slice(0, 1);
      
      // Combine the limited meanings for Adjective
      if (aMeanings.length > 0 || sMeanings.length > 0) {
        groupedMeanings['Adjective'] = [...aMeanings, ...sMeanings]; // This will have at most 4 total
      }
      
      // Process other parts of speech normally
      data.part_of_speech.forEach((pos, index) => {
        if (pos !== 'a' && pos !== 's') {
          const normalizedPos = mapPartOfSpeech(pos);
          if (!groupedMeanings[normalizedPos]) {
            groupedMeanings[normalizedPos] = [];
          }
          const meanings = data.english_meanings[index] || [];
          groupedMeanings[normalizedPos].push(...meanings.slice(0, 3));
        }
      });
    } else {
      // Normal processing when not both 's' and 'a'
      normalizedPOS.forEach((pos, index) => {
        if (!groupedMeanings[pos]) {
          groupedMeanings[pos] = [];
        }
        
        // Add meanings for this part of speech (if available)
        const meanings = data.english_meanings[index] || [];
        groupedMeanings[pos].push(...meanings.slice(0, 3));
      });
    }
    
    // Prepare the en_meaning object
    const limitedMeanings: { [key: string]: string } = {};
    
    Object.keys(groupedMeanings).forEach(pos => {
      if (groupedMeanings[pos].length > 0) {
        limitedMeanings[pos] = groupedMeanings[pos].join(',');
      }
    });
    
    // Process the translation data
    const wordCreate: WordCreate = {
      word: data.word,
      ch_meaning: [data.translated_word],
      part_of_speech: Array.from(new Set(normalizedPOS)), // Remove duplicates
      en_meaning: limitedMeanings,
      translated: 1,
    };
    return wordCreate;
  } catch (error) {
    const wordCreate: WordCreate = {
      word: word,
      en_meaning: {},
      ch_meaning: [],
      part_of_speech: [],
      translated: 0,
    };
    return wordCreate;
  }
};