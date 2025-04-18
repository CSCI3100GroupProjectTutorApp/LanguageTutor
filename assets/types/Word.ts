export interface WordCreate {
  word: string;
  en_meaning?: { [key: string]: string }
  ch_meaning?: string[];
  part_of_speech?: string[];
  translated?: number;
}

export interface WordUpdate {
  word: string;
  en_meaning?: { [key: string]: string };
  ch_meaning?: string[];
  part_of_speech?: string[];
  translated?: number;
}

export interface Word {
  wordid: number;
  word: string;
  en_meaning: {[key: string]: string};
  ch_meaning: string[];
  part_of_speech: string[];
  wordtime: string;
  synced?: number;
  translated?: number;
}